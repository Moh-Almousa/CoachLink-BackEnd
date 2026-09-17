from rest_framework import serializers
from ..models import User,  CoachProfile, PlayerProfile, AdminProfile, CoachRating

import time
# ===== تسجيل مستخدم محلي =====
class LocalRegisterSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        start = time.perf_counter()
        password = validated_data.pop('password', None)
        print(
                            f"pop password : "
                            f"{time.perf_counter() - start:.4f} seconds"
                        )
        start=time.perf_counter()
        instance = self.Meta.model(**validated_data)
        print(
                    f"instanc =  **validated_data :"
                    f"{time.perf_counter() - start:.4f} seconds"
                )
        start=time.perf_counter()
        if password:
            instance.set_password(password)
        instance.save()
        print(
                    f"hash pass and save instance: "
                    f"{time.perf_counter() - start:.4f} seconds"
                )
        start=time.perf_counter()
        if instance.role == User.Role.COACH:
            CoachProfile.objects.create(user=instance)
        elif instance.role == User.Role.PLAYER:
            PlayerProfile.objects.create(user=instance)
        else:
            AdminProfile.objects.create(user=instance)
        print(
                    f"user -> profile (plauer/admin/coach): "
                    f"{time.perf_counter() - start:.4f} seconds"
                )
        return instance
        

    class Meta:
        model = User
        fields = [ 'id', 'full_name', 'password', 'birth_date', 'email', 'role',
                  'gender' , 'auth_provider', 'provider_user_id', 'status', 'created_at']
        extra_kwargs = {
            'provider_user_id': {'required': False},
            'auth_provider': {'default': User.AuthProvider.LOCAL},
            'status': {'default': False},
            'id': {'read_only': True},
            'password': {'write_only': True},
            'created_at': {'read_only': True},
        }

# ===== إرجاع بيانات المستخدم كاملةل users =====
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role', 'gender', 'birth_date',
                  'auth_provider', 'provider_user_id', 'status', 'created_at']

# ===== مصادقة غوغل: بس access_token =====
class GoogleAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField()   
# ===== إكمال بيانات الحساب بعد تسجيل الدخول عبر غوغل =====
class CompleteGoogleProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role", "gender", "birth_date"]

    def validate(self, attrs):
        user = self.instance

        if user.auth_provider != User.AuthProvider.GOOGLE:
            raise serializers.ValidationError(
                "This endpoint is only for Google accounts."
            )

        if user.role is not None:
            raise serializers.ValidationError(
                "Profile has already been completed."
            )

        return attrs
    def update(self, instance, validated_data):
        instance.role = validated_data["role"]
        instance.gender = validated_data["gender"]
        instance.birth_date = validated_data["birth_date"]
        instance.save()

        if instance.role == User.Role.COACH:
            CoachProfile.objects.create(user=instance)

        elif instance.role == User.Role.PLAYER:
            PlayerProfile.objects.create(user=instance)
        else:
            AdminProfile.objects.create(user=instance)
        return instance
# ===== تسجيل دخول محلي =====
class LocalLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# ===== التحقق من OTP =====
class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)


class PasswordResetInSettingSerializer(serializers.Serializer):
    current_password=serializers.CharField(write_only=True, min_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8)
   