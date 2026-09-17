from urllib import request
from decimal import Decimal
from django.db.models import Prefetch, Avg, Count, OuterRef, Subquery, Q ,Sum,F, Min, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsCoach, IsVerifiedCoach ,IsPlayer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from subscriptions.models import SubscriptionPlayer ,SubscriptionPackage ,Payment
from logs.models import WorkoutLog, NutritionLog
from programs.models import ProgramPlanExercise
from nutritions.models import NutritionPlan
from ..models import Certificate, CoachTransformation ,CoachProfile ,CoachRating
from ..serializers.coach_serializers import (
    CoachCertificateSerializer,CoachProfessionalInformationSerializer,
    CoachProfileSerializer, CoachCertificateDisplaySerializer,
    CoachTransformationSerializer,CoachCardSerializer,CoachDetailSerializer,
    PlayerInvitationSerializer ,CoachDashboardSerializer ,CoachPlayerCardSerializer,
    CoachPlayersStatsSerializer)
from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

class CoachCertificateView(APIView):
    permission_classes = [IsAuthenticated , IsCoach]
    @extend_schema(
        summary="Get Coach Certificates",
        description = "ارجاع شهادات الكوتش ، خاصة للكوتشات",
        responses={200:CoachCertificateDisplaySerializer(many=True)}
   ) 
    def get(self, request):
        coach = request.user.coach_profile
        certificates = Certificate.objects.filter(coach_profile=coach)
        serializer = CoachCertificateDisplaySerializer(certificates, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    @extend_schema(
        summary="Upload Coach Certificate",
        description= "رفع شهادة الكوتش ، خاصة للكوتشات",
        request=CoachCertificateSerializer,
        responses={200:OpenApiResponse(description="The certificate has been successfully uploaded.It will be reviewed by Admin.")}
    )
    def post(self, request):
        serializer = CoachCertificateSerializer(data=request.data)
        if serializer.is_valid():
            certificate = serializer.validated_data['certificate_pdf_url']
            # احفظ الشهادة في ملف المدرب
            coach = request.user.coach_profile
            certificate_instance = Certificate.objects.create(
                coach_profile=coach,
                certificate_pdf_url=certificate,
                verification_status=Certificate.VerificationStatus.WAITING
            )
            return Response({"message": "The certificate has been successfully uploaded.It will be reviewed by Admin."}
                            , status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CoachTransformationView(APIView):
    permission_classes = [IsAuthenticated , IsVerifiedCoach]
    @extend_schema(
        summary="Get Album of Coach",
        description="ارجاع صور البوم تحولات لاعبين الكوتش ، خاصة للكوتشات الموثقين",
        responses={200:CoachTransformationSerializer(many=True)}
    )
    def get(self, request):
        coach = request.user.coach_profile
        transformations = CoachTransformation.objects.filter(coach=coach)
        serializer = CoachTransformationSerializer(transformations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    @extend_schema(
        summary="Upload Transformation Image",
        description="رفع صورة تحول لاعب في البوم الكوتش ، خاصة للكوتشات الموثوقين",
        request=CoachTransformationSerializer,
        responses={201:CoachTransformationSerializer(many=True)}
    )
    def post(self, request):
        serializer = CoachTransformationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            coach = request.user.coach_profile
            serializer.save(coach=coach)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @extend_schema(
        summary="Update one Transformation Image",
        description="تعديل صورة واحدة او المدة او صوتين من الالبوم ، خاصة للكوتشات الموثوقين",
        request=CoachTransformationSerializer,
        responses={200:CoachTransformationSerializer(many=True)}
    )   
    def patch(self, request,pk):
        coach = request.user.coach_profile
        try:
            transformation = CoachTransformation.objects.get(id=pk, coach=coach)
        except CoachTransformation.DoesNotExist:
            return Response({"error": "Transformation not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CoachTransformationSerializer(transformation, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @extend_schema(
        summary="Update all Transformation Image",
        description="تعديل الالبوم كامل ، خاصة للكوتشات الموثوقين",
        request=CoachTransformationSerializer,
        responses={200:CoachTransformationSerializer(many=True)}
    ) 
    def put(self, request, pk):
        coach = request.user.coach_profile
        try:
            transformation = CoachTransformation.objects.get(id=pk, coach=coach)
        except CoachTransformation.DoesNotExist:
            return Response({"error": "Transformation not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CoachTransformationSerializer(transformation, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @extend_schema(
        summary="Delete one Transformation Image",
        description="حذف الالبوم ، خاصة للكوتشات الموثوقين",
        responses={200:OpenApiResponse(description = "Transformation deleted successfully.")}
    ) 
    def delete(self, request, pk):
        coach = request.user.coach_profile
        try:
            transformation = CoachTransformation.objects.get(id=pk, coach=coach)
        except CoachTransformation.DoesNotExist:
            return Response({"error": "Transformation not found."}, status=status.HTTP_404_NOT_FOUND)
        transformation.delete()
        return Response({"message": "Transformation deleted successfully."}, status=status.HTTP_200_OK)

class CoachProfileView(APIView):
    permission_classes = [IsAuthenticated , IsVerifiedCoach]
    @extend_schema(
        summary="Get coach profile",
        description="Retrieve the profile information of the authenticated and verified coach.",
        responses={200:CoachProfileSerializer}
    )
    def get(self, request):
        coach = request.user.coach_profile
        serializer = CoachProfileSerializer(coach, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    @extend_schema(
            summary="Update coach professional profile",
            description="Update the profile information of the authenticated and verified coach.",
            request = CoachProfessionalInformationSerializer,
            responses= {200:OpenApiResponse(description="Professional profile has been successfully updated.")}
    )
    def patch(self, request):
        coach = request.user.coach_profile
        serializer = CoachProfessionalInformationSerializer(coach, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Professional profile has been successfully updated."},
                        status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CoachListView(APIView):
    permission_classes = [IsAuthenticated , IsPlayer]
    @extend_schema(
        summary="Get List Card of Coaches",
        description="عرض قائمة كروت الكوتشات , خاصة للاعبين",
        responses={200:CoachCardSerializer(many=True)}
    )
    def get(self, request):
        ratings=(CoachRating.objects.filter(coach=OuterRef('pk'))
                                    .values('coach')
                                    .annotate(avg_rating=Avg('rating') ,
                                              count_rating=Count('rating')))
        players_sq = (SubscriptionPlayer.objects.filter(package__coach=OuterRef('pk'))
                                                    .values('package__coach')
                                                    .annotate(count=Count('player',distinct=True)))
        coaches = (CoachProfile.objects
                   .select_related('user')
                   .filter(verification_status=CoachProfile.VerificationStatus.ACCEPTED)
                   .annotate(
                       avr_rating=Subquery(ratings.values('avg_rating')),
                       Reviews=Coalesce(Subquery(ratings.values('count_rating')), 0),
                       totalplayer=Coalesce(Subquery(players_sq.values('count')), 0),
                   ))

        search = request.query_params.get('search', '').strip()
        if search:
            search_filter = Q()
            for word in search.split():
                search_filter &= (
                    Q(user__full_name__icontains=word) |
                    Q(specialization__icontains=word) |
                    Q(user__email__icontains=word)
                )
            coaches = coaches.filter(search_filter)

        serializer = CoachCardSerializer(coaches, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class CoachDetailView(APIView):
    permission_classes = [IsAuthenticated , IsPlayer]
    @extend_schema(
            summary="Get Coach Detail",
            description="ارجاع تفاصسل كوتش معين ، خاصة للاعبين",
            responses={200:CoachDetailSerializer}
    )
    def get(self, request, pk):
        try:
            coach=(CoachProfile.objects
                   .select_related('user')
                   .prefetch_related('transformations',
                                     Prefetch('packages',
                                              queryset=SubscriptionPackage.objects.filter(is_active=True)),
                                     Prefetch('ratings',
                                              queryset=CoachRating.objects.select_related('player__user').order_by('-created_at')))
                                     .get(pk=pk,verification_status=CoachProfile.VerificationStatus.ACCEPTED))
        except CoachProfile.DoesNotExist:
            return Response({"error": "Coach not found."}, status=status.HTTP_404_NOT_FOUND)
        rating=coach.ratings.aggregate(avr_rating=Avg('rating'), Reviews=Count('id')) 
        coach.avr_rating = rating['avr_rating']
        coach.Reviews= rating['Reviews']
        coach.totalplayer=(SubscriptionPlayer.objects
                           .filter(package__coach=coach)
                           .values('player')
                           .distinct()
                           .count())
        serializer=CoachDetailSerializer(coach,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

class PlayerInvitationView(APIView):
    permission_classes = [IsAuthenticated , IsVerifiedCoach]
    @extend_schema(
        summary="Send Invitation Email to Player",
        description="ارسال دعوة لاعب للانضمام للمنسة واشتراكه عند الكوتش ، خاصة للكوتشات الموثوقين",
        request=PlayerInvitationSerializer,
        responses={200:OpenApiResponse(description="Invitation email sent successfully.")}
    )
    def post(self, request):
        serializer = PlayerInvitationSerializer(data=request.data)
        if serializer.is_valid():
            player_email = serializer.validated_data['email']
            coach = request.user.coach_profile
            coach_name = coach.user.full_name
            coach_email = coach.user.email
            invitation_link= "http://localhost:3000/"
            send_mail(subject=f'{coach_name} invited you to join CoachLink',
            message=(
                f'Hello,\n\n'
                f'You have been invited by {coach_name} '
                f'to join CoachLink.\n\n'
                f'Join the platform using the following link:\n'
                f'{invitation_link}\n\n'
                f'After joining, search for your coach using this email:\n'
                f'{coach_email}\n\n'
                f'Thank you.'
                    ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[player_email],
            fail_silently=False,
                        )       
            return Response({"message": "Invitation email sent successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def get_coach_recent_activity(coach, limit=5):
    """
    بتجمع آخر نشاطات لاعبين هاد الكوتش من 4 مصادر مختلفة، وبترجعهم
    بشكل موحّد مرتب زمنياً تنازلي. كل المصادر مفلترة عبر coach مباشرة
    (WorkoutLog/NutritionLog عبر سلسلة الخطة->الكوتش، والخطتين مباشرة)
    - يعني بس نشاطات مرتبطة بخطط أنشأها هاد الكوتش تحديداً.
    """
    activities = []

    # 1) تمارين نُفّذت
    workout_logs = (WorkoutLog.objects
        .filter(program_day_exercise__program_day__week__plan__coach=coach)
        .exclude(date_day__isnull=True)
        .select_related('program_day_exercise__program_day__week__plan__player__user')
        .order_by('-date_day')[:limit])
    for log in workout_logs:
        player = log.program_day_exercise.program_day.week.plan.player
        activities.append({
            'type': 'workout',
            'player_name': player.user.full_name,
            'player_image': player.image_profile_url.url if player.image_profile_url else None,
            'message': f"{player.user.full_name} logged a workout",
            'timestamp': log.date_day,
        })

    # 2) وجبات نُفّذت
    nutrition_logs = (NutritionLog.objects
        .filter(meal__day__week__plan__coach=coach)
        .exclude(date_day__isnull=True)
        .select_related('meal__day__week__plan__player__user')
        .order_by('-date_day')[:limit])
    for log in nutrition_logs:
        player = log.meal.day.week.plan.player
        activities.append({
            'type': 'meal',
            'player_name': player.user.full_name,
            'player_image': player.image_profile_url.url if player.image_profile_url else None,
            'message': f"{player.user.full_name} logged a meal",
            'timestamp': log.date_day,
        })

    # 3) برامج تمارين جديدة اتعملت
    new_programs = (ProgramPlanExercise.objects
        .filter(coach=coach)
        .select_related('player__user')
        .order_by('-created_at')[:limit])
    for plan in new_programs:
        activities.append({
            'type': 'new_program',
            'player_name': plan.player.user.full_name,
            'player_image': plan.player.image_profile_url.url if plan.player.image_profile_url else None,
            'message': f"{plan.player.user.full_name} was assigned a new workout program",
            'timestamp': plan.created_at,
        })

    # 4) خطط تغذية جديدة اتعملت
    new_nutrition_plans = (NutritionPlan.objects
        .filter(coach=coach)
        .select_related('player__user')
        .order_by('-created_at')[:limit])
    for plan in new_nutrition_plans:
        activities.append({
            'type': 'new_nutrition_plan',
            'player_name': plan.player.user.full_name,
            'player_image': plan.player.image_profile_url.url if plan.player.image_profile_url else None,
            'message': f"{plan.player.user.full_name} was assigned a new nutrition plan",
            'timestamp': plan.created_at,
        })

    # نجمع الأربعة مصادر ونرتبهم زمنياً، ونقص لآخر limit فقط
    activities.sort(key=lambda a: a['timestamp'], reverse=True)
    return activities[:limit]


class CoachDashboardView(APIView):
    permission_classes = [IsAuthenticated , IsVerifiedCoach]
    @extend_schema(
        summary="Get Coach Dashboard Data",
        description="ارجاع لوحة تحكم الكوتش ، خاصة للكوتشات الموثوقة",
        responses={200:CoachDashboardSerializer}
    )
    def get(self, request):
        coach = request.user.coach_profile
        full_name = coach.user.full_name
        coach_status = coach.verification_status
        totalplayer= (SubscriptionPlayer.objects.filter(package__coach=coach)
                    .values('player')
                        .distinct()
                        .count()
                    )
        activeplayer= (SubscriptionPlayer.objects.filter(package__coach=coach, status=SubscriptionPlayer.Status.ACTIVE)
                    .values('player').distinct().count()
                    )
        expiring_soon=(SubscriptionPlayer.objects.filter(
            package__coach=coach,
            status=SubscriptionPlayer.Status.ACTIVE,
            end_date__gte=timezone.now(),
            end_date__lte=timezone.now() + timedelta(days=5))
                       .values('player').distinct().count()
                       )
        revenue=(Payment.objects.filter(coach=coach,
                                        payment_status=Payment.Status.COMPLETED,
                                        created_at__year=timezone.now().year,
                                        created_at__month=timezone.now().month)
                                        .aggregate(total_revenue=Coalesce(Sum('coach_profit'), Decimal('0')))
                                        ['total_revenue'])
        recent_activity=get_coach_recent_activity(coach, limit=5)
        data={
            "full_name": full_name,
            "status": coach_status,
            "totalplayer": totalplayer,
            "activeplayer": activeplayer,
            "expiring_soon": expiring_soon,
            "revenue": revenue,
            "recent_activity": recent_activity
        }
        serializer = CoachDashboardSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CoachMyPlayers(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedCoach]
    @extend_schema(
        summary="Get My Players of Coach",
        description="ارجاع قائمة لاعبين الكوتش ، خاصة للكوتشات الموثوقين",
        responses={
            200:inline_serializer(
                name="CoachPlayersResponse",
                fields={
                    "coach_id":serializers.IntegerField(),
                    "statistics":CoachPlayerCardSerializer(many=True),
                    "players_cards":CoachPlayersStatsSerializer(many=True)
                }
            )
        }
    )
    def get(self, request):
        coach = request.user.coach_profile
        totalplayer= (SubscriptionPlayer.objects.filter(package__coach=coach)
                            .values('player')
                                .distinct()
                                .count()
                            )
        activeplayer= (SubscriptionPlayer.objects.filter(package__coach=coach, status=SubscriptionPlayer.Status.ACTIVE)
                            .values('player').distinct().count()
                            )
        new_players_this_month = (
            SubscriptionPlayer.objects.filter(package__coach=coach)
            .values('player')
            .annotate(first_subscription=Min('created_at'))
            .filter(first_subscription__year=timezone.now().year,
                    first_subscription__month=timezone.now().month)
            .count()
        )

        subs = (SubscriptionPlayer.objects
                .filter(package__coach=coach)
                .select_related('player__user', 'package')
                .annotate(priority=Case(
                    When(status=SubscriptionPlayer.Status.ACTIVE, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                ))
                .order_by('player_id', 'priority', '-end_date'))

        cards = [] 
        seen_players = set()
        for sub in subs:
            if sub.player_id not in seen_players:
                cards.append(sub)
                seen_players.add(sub.player_id)

        expired_subscriptions = sum(1
                                    for card in cards if card.status == SubscriptionPlayer.Status.FINISH)
        data={
            "totalplayer": totalplayer,
            "activeplayer": activeplayer,
            "new_players_this_month": new_players_this_month,
            "expired_subscriptions": expired_subscriptions
        }           
        cards_serializer = CoachPlayerCardSerializer(cards, many=True, context={'request': request})
        stats_serializer = CoachPlayersStatsSerializer(data)
        return Response({
            "coach_id": coach.id,
            "statistics": stats_serializer.data,
            "players_cards": cards_serializer.data,
        }, status=status.HTTP_200_OK)
