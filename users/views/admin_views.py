import calendar

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsAdmin, IsVerifiedCoach
from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..utils import generate_otp, send_otp_email
from django.core.mail import send_mail
from CoachLink.settings import EMAIL_HOST_USER ,MAX_OTP_TRY
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import CoachProfile,Certificate,User, PlayerProfile
from subscriptions.models import SubscriptionPlayer
from ..serializers.admin_serializers import (
    CertificateAuthenticationSerializer,
    CertificateReviewSerializer ,AdminDashboardSerializer
)

def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)

class CertificateAuthenticationView(APIView):
    permission_classes = [IsAuthenticated , IsAdmin]
    @extend_schema(
        summary="Get All Certificats",
        description="ارجاع جميع شهادات الكوتشات ، خاصة للادمن",
        responses={200:CertificateAuthenticationSerializer(many =True)}
    )
    def get(self, request):
        certificates = Certificate.objects.all()
        serializer = CertificateAuthenticationSerializer(certificates, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    @extend_schema(
    summary="Certificate verification",
    description="تدقيق الشهادة من قبل الادمن ، خاصة للأدمن",
    request=CertificateReviewSerializer,
    responses={200:OpenApiResponse(description="Certificate authentication status updated successfully."),
               400:OpenApiResponse(description="Certificate not found or invalid data")}
    )
    def post(self, request):
        serializer = CertificateReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
        certificate_id = serializer.validated_data['id']
        verification_status = serializer.validated_data['verification_status']
        rejection_reason = serializer.validated_data.get('rejection_reason')
        note = serializer.validated_data.get('note')

        try:
            certificate = Certificate.objects.get(id=certificate_id)
        except Certificate.DoesNotExist:
            return Response({"error": "Certificate not found."}, status=status.HTTP_404_NOT_FOUND)

        certificate.verification_status = verification_status
        certificate.reviewed_by = request.user
        if verification_status == Certificate.VerificationStatus.REJECTED:
            certificate.rejection_reason = rejection_reason
            certificate.note = note
        else:
            certificate.rejection_reason = None
            certificate.note = None
        certificate.verified_at = timezone.now()
        certificate.save()
        
        coach_profile = certificate.coach_profile
        if coach_profile.verification_status != CoachProfile.VerificationStatus.ACCEPTED:
            if verification_status == Certificate.VerificationStatus.ACCEPTED:
                coach_profile.verification_status = CoachProfile.VerificationStatus.ACCEPTED
            elif verification_status == Certificate.VerificationStatus.REJECTED:
                coach_profile.verification_status = CoachProfile.VerificationStatus.REJECTED
            coach_profile.save(update_fields=["verification_status"])
            
        email_message = (
            f'Your certificate has been {certificate.get_verification_status_display()}.\n'
            f'Reason: {rejection_reason or "N/A"}'
        )
        if note:
            email_message += f'\nAdditional details: {note}'

        send_mail(
            subject='Certificate Verification Result',
            message=email_message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[certificate.coach_profile.user.email],
            fail_silently=False,
        )
        return Response({"message": "Certificate authentication status updated successfully."},
                        status=status.HTTP_200_OK)
        
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    @extend_schema(
        summary="Get Admin Dashboard Data",
        description="ارجاع بيانات لوحة تحكم الأدمن ، خاصة للأدمن",
        responses={200:AdminDashboardSerializer}
    )
    def get(self, request):
        total_users = User.objects.count()
        total_coaches = CoachProfile.objects.count()
        total_players = PlayerProfile.objects.count()
        active_subscriptions = SubscriptionPlayer.objects.filter(status=SubscriptionPlayer.Status.ACTIVE).count()
        waiting_certificates = Certificate.objects.filter(verification_status=Certificate.VerificationStatus.WAITING).count()

        # حساب نمو المستخدمين على مدى الأشهر الستة الماضية (من الأقدم للأحدث)
        current_month_start = timezone.now().replace(day=1)
        user_growth = []
        for i in range(5, -1, -1):
            month_start = add_months(current_month_start, -i)
            month_end = add_months(month_start, 1)
            new_users = User.objects.filter(created_at__gte=month_start, created_at__lt=month_end).count()
            user_growth.append({
                "month": month_start.strftime("%Y-%m"),
                "new_users": new_users
            })

        dashboard_data = {
            "total_users": total_users,
            "total_coaches": total_coaches,
            "total_players": total_players,
            "active_subscriptions": active_subscriptions,
            "waiting_certificates": waiting_certificates,
            "user_growth": user_growth
        }

        serializer = AdminDashboardSerializer(dashboard_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
