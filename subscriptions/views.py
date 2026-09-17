import calendar
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SubscriptionPackage, Payment, SubscriptionPlayer
from chats.models import ChatConversation
from .serializers import SubscriptionPackagesSerializer, CreatePaymentSerializer
from users.permissions import  IsVerifiedCoach ,IsPlayer
from rest_framework.permissions import IsAuthenticated
from users.models import CoachProfile,User
from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

stripe.api_key = settings.STRIPE_SECRET_KEY

#! stripe listen --forward-to localhost:8000/api/subscriptions/webhook/

# نسبة أرباح المنصة الافتراضية من كل عملية دفع
PLATFORM_PERCENTAGE = Decimal('15')


def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)


class SubscriptionPackageView(APIView):
    permission_classes = [IsAuthenticated,IsVerifiedCoach]
    @extend_schema(
        summary="Get all subscription packages for coach",
        description="ارجاع كل الباقات التابعة للكوتش ، خاصة للكوتش الموثوق",
        responses={200:SubscriptionPackagesSerializer(many=True)}
    )
    def get(self, request):
        coach = request.user.coach_profile
        packages = SubscriptionPackage.objects.filter(coach=coach, is_active=True)
        serializer = SubscriptionPackagesSerializer(packages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @extend_schema(
        summary="Create a new subscription package for coach",
        description="انشاء باقة اشتراك جديدة ، خاصة للكوتشات الموثوقين",
        request=SubscriptionPackagesSerializer,
        responses={
            201:SubscriptionPackagesSerializer,
            400:OpenApiResponse(description="Bad Request")
        }
   )
    def post(self, request):
        coach = request.user.coach_profile
        serializer = SubscriptionPackagesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(coach=coach)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @extend_schema(
        summary="Update a subscription package for coach",
        description="تحديث باقة اشتراك موجودة ، خاصة للكوتشات الموثوقين",
        request=SubscriptionPackagesSerializer,
        responses={
            200:SubscriptionPackagesSerializer,
            400:OpenApiResponse(description="Bad Request"),
            404:OpenApiResponse(description="Package not found")
        }
    )
    def patch(self, request,pk):
        coach = request.user.coach_profile
        try:
            package = SubscriptionPackage.objects.get(id=pk, coach=coach)
        except SubscriptionPackage.DoesNotExist:
            return Response({'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubscriptionPackagesSerializer(package, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @extend_schema(
        summary="Delete a subscription package for coach",
        description="حذف باقة اشتراك موجودة عند الكوتش ، خاصة للكوتشات الموثوقين",
        responses={
            200:OpenApiResponse(description="Package deleted successfully., deactivated: False"),\
            200:OpenApiResponse(description="This package has existing payments or subscriptions, so it was deactivated instead of deleted., deactivated: True"),
            404:OpenApiResponse(description="Package not found"),
        }
    )
    def delete(self, request,pk):
        coach = request.user.coach_profile
        try:
            package = SubscriptionPackage.objects.get(id=pk, coach=coach)
        except SubscriptionPackage.DoesNotExist:
            return Response({'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            package.delete()
            return Response({'message': 'Package deleted successfully.', 'deactivated': False},
                             status=status.HTTP_200_OK)
        except ProtectedError:
            # الباقة مرتبطة بدفعات/اشتراكات فعلية (on_delete=PROTECT بـ Payment/SubscriptionPlayer)
            # فحذفها فعليًا بيكسر تاريخ الدفعات - بنكتفي بتعطيلها (بتختفي من قائمة الكوتش
            # لأنو الـ GET أصلاً بيفلتر is_active=True) بدل ما نحذفها فعليًا من القاعدة.
            package.is_active = False
            package.save(update_fields=['is_active'])
            return Response(
                {'message': 'This package has existing payments or subscriptions, so it was deactivated instead of deleted.',
                 'deactivated': True},
                status=status.HTTP_200_OK,
            )


class CreatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPlayer]
    @extend_schema(
        summary="create a new payment for a subscription package",
        description="انشاء سجل دفع لباقة اشتراك ، خاصة للاعبين",
        request=CreatePaymentSerializer,
        responses={
            200:inline_serializer(
                name="PaymentResponse",
                fields={
                    "checkout_url":serializers.URLField(),
                    "payment_id":serializers.IntegerField()
                }
            ),
            400:OpenApiResponse(description="You already have an active subscription. Finish it before subscribing to a new coach."),
            404:OpenApiResponse(description="Package not found or inactive.")
        }
    )
    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            package = SubscriptionPackage.objects.select_related('coach').get(
                id=serializer.validated_data['package_id'], is_active=True
            )
        except SubscriptionPackage.DoesNotExist:
            return Response({'error': 'Package not found or inactive.'}, status=status.HTTP_404_NOT_FOUND)

        player = request.user.player_profile
        if SubscriptionPlayer.objects.filter(player=player, status=SubscriptionPlayer.Status.ACTIVE).exists():
            return Response(
                {'error': 'You already have an active subscription. Finish it before subscribing to a new coach.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        price = package.price
        # الأرباح لسا ما محسوبة هون قصدًا: الدفع لسا PENDING ومش مؤكد إنو رح ينجح.
        # الحساب الفعلي وتخزينه بيصير بالـ webhook (stripe_webhook) لما Stripe يأكد نجاح الدفع.
        payment = Payment.objects.create(
            player=player,
            coach=package.coach,
            package=package,
            platform_percentage=PLATFORM_PERCENTAGE,
            platform_profit=Decimal('0'),
            coach_profit=Decimal('0'),
            payment_provider=Payment.Provider.STRIPE,
            payment_status=Payment.Status.PENDING,
        )

        checkout_session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(price * 100),
                    'product_data': {
                        'name': f'{package.name} - {package.number_month} month(s) - {package.coach.user.full_name}',
                    },
                },
                'quantity': 1,
            }],
            success_url='http://localhost:3000/payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:3000/payment/cancel',
            metadata={'payment_id': payment.id},
        )

        payment.transaction_id = checkout_session.id
        payment.save(update_fields=['transaction_id'])

        return Response(
            {'checkout_url': checkout_session.url, 'payment_id': payment.id},
            status=status.HTTP_201_CREATED,
        )


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        # event['data']['object'] من نوع StripeObject، وبنسخة stripe-python المثبتة
        # هون هاد النوع ما بيرث من dict وما عندو .get() -> AttributeError.
        # to_dict() بيحولها (وكل شي جواها متل metadata) لـ dict عادي فيه .get().
        session = event['data']['object'].to_dict()
        payment_id = session.get('metadata', {}).get('payment_id')
        try:
            with transaction.atomic():
                # select_for_update: قفل صف الـ Payment لحتى ما توصلين نسختين من نفس
                # الـ webhook (Stripe ممكن يعيد الإرسال) ويعالجوه سوا فيصير تكرار.
                payment = Payment.objects.select_for_update().select_related('package').get(id=payment_id)

                if payment.payment_status != Payment.Status.COMPLETED:
                    # الأرباح تُحسب هون بس، بعد ما نتأكد إنو الدفع نجح فعليًا عند Stripe.
                    price = payment.package.price
                    platform_profit = (price * payment.platform_percentage / Decimal('100')).quantize(Decimal('0.01'))
                    coach_profit = price - platform_profit

                    payment.payment_status = Payment.Status.COMPLETED
                    payment.platform_profit = platform_profit
                    payment.coach_profit = coach_profit
                    payment.save(update_fields=['payment_status', 'platform_profit', 'coach_profit'])

                    start_date = timezone.now()
                    try:
                        SubscriptionPlayer.objects.create(
                            package=payment.package,
                            player=payment.player,
                            payment=payment,
                            start_date=start_date,
                            end_date=add_months(start_date, payment.package.number_month),
                            status=SubscriptionPlayer.Status.ACTIVE,
                        )
                        # الشات هو الوسيلة الوحيدة يلي بتقابل الكوتش واللاعب ببعض،
                        # فبمجرد ما الاشتراك ينفعل لازم تنعمل قناة دردشة فاضية بينهم
                        # فوراً (بدل ما تنتظر أول رسالة). get_or_create لأنو ممكن
                        # يكونوا اشتركوا سابقاً وانتهى الاشتراك، فالمحادثة أصلاً موجودة
                        # (UniqueConstraint على coach+player بـ ChatConversation).
                        ChatConversation.objects.get_or_create(coach=payment.coach, player=payment.player)
                    except IntegrityError:
                        # اللاعب صار عندو اشتراك نشط تاني بالفترة بين إنشاء الدفعة واكتمالها
                        # (مثلاً فتح صفحتي دفع بنفس الوقت). الدفع نجح فعلياً عند Stripe، فلازم
                        # مراجعة يدوية (استرجاع المبلغ أو ربطه باشتراك تاني) بدل ما نخسر الفلوس بصمت.
                        pass
        except Payment.DoesNotExist:
            return HttpResponse(status=404)

    return HttpResponse(status=200)

