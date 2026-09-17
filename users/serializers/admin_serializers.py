from rest_framework import serializers
from ..models import User,  CoachProfile, PlayerProfile, AdminProfile ,Certificate

# بيانات الكوتش المختصرة، مضمّنة جوا كل شهادة عشان جدول الأدمن يقدر يعرض
# اسم/إيميل/صورة الكوتش بدون طلب إضافي منفصل لكل شهادة.
class CoachProfileMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CoachProfile
        fields = ['id', 'full_name', 'email', 'image_profile_url']

class CertificateAuthenticationSerializer(serializers.ModelSerializer):
    coach_profile = CoachProfileMiniSerializer(read_only=True)

    class Meta:
        model = Certificate
        fields = ['id', 'coach_profile', 'certificate_pdf_url', 'verification_status',
                  'rejection_reason', 'note', 'verified_at', 'created_at']

class CertificateReviewSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    verification_status = serializers.ChoiceField(
        choices=Certificate.VerificationStatus.choices
    )
    rejection_reason = serializers.ChoiceField(
        choices=Certificate.RejectionReason.choices, required=False, allow_null=True
    )
    # نص حر اختياري - بيستخدم بشكل رئيسي لما rejection_reason = "Other"
    # (تفاصيل الرفض يلي القيم الثابتة فوق ما بتغطيها).
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=500)

    def validate(self, data):
        if data['verification_status'] == Certificate.VerificationStatus.REJECTED \
                and not data.get('rejection_reason'):
            raise serializers.ValidationError(
                {"rejection_reason": "Rejection reason is required when rejecting a certificate."}
            )
        return data
    
class UserGrowthItemSerializer(serializers.Serializer):
    month = serializers.CharField()
    new_users = serializers.IntegerField()

class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_coaches = serializers.IntegerField()
    total_players = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    waiting_certificates = serializers.IntegerField()
    user_growth = UserGrowthItemSerializer(many=True)