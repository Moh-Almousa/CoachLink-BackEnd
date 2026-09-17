from django.utils import timezone
from django.db import transaction
from random import  random
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers.auth_serializers import (CompleteGoogleProfileSerializer,VerifyOtpSerializer,LocalLoginSerializer,
    LocalRegisterSerializer,GoogleAuthSerializer,PasswordResetConfirmSerializer,UserSerializer,PasswordResetInSettingSerializer
)
from ..utils import generate_otp, send_otp_email, get_google_user_info
from ..models import Otp, User 
from django.core.mail import send_mail
from CoachLink.settings import EMAIL_HOST_USER ,MAX_OTP_TRY
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers
import time
from ..tasks import send_to_email_task
class LocalRegisterView(APIView):
    @extend_schema(
        summary="ٌRegister a new user for local ",
        description="انشاء حساب جديد محلي وارسال كود تحقق لتوثيق الحساب عبر البريد الاكتروني ",
        request=LocalRegisterSerializer,
        responses={201:OpenApiResponse(description="OTP sent successfully."),
                   400:OpenApiResponse(description="Invalid data")}
    )
    def post(self, request):
        # total_start = time.perf_counter()
        # 1. Serializer validation
        # start = time.perf_counter()
        serializer = LocalRegisterSerializer(data=request.data)
        if serializer.is_valid():
        #     print(
        #     f"Serializer validation: "
        #     f"{time.perf_counter() - start:.4f} seconds"
        # )
            # transaction.atomic: لو فشل إرسال الإيميل (مثلاً انقطاع SMTP مؤقت)،
            # لازم نلغي إنشاء المستخدم وOTP كمان - وإلا بيضل حساب "معلّق" بالقاعدة
            # (مسجّل بس ماله أي OTP فعلي وصل، وما فيك تسجّل بنفس الإيميل مرة تانية)
            with transaction.atomic():
                # start = time.perf_counter()
                user=serializer.save()
                # print(
                #     f"Create user/profile: "
                #     f"{time.perf_counter() - start:.4f} seconds"
                # )
                # 3. Delete old OTP
                # start = time.perf_counter()
                Otp.objects.filter(user=user).delete()  # Delete any existing OTPs for the user
                # print(
                #     f"Delete old OTP: "
                #     f"{time.perf_counter() - start:.4f} seconds"
                # )
                 # 4. Generate + Save OTP
                # start = time.perf_counter()
                code=generate_otp()
                Otp.objects.create(user=user, otp_code=code ,
                                   expires_at=timezone.now() + timezone.timedelta(minutes=5))
                # print(
                #     f"Generate + save OTP: "
                #     f"{time.perf_counter() - start:.4f} seconds"
                # )
                # 5. Send Email
                # start = time.perf_counter()
                user_email=user.email
                send_to_email_task.delay(user_email, code)
                # print(
                #     f"queue task: "
                #     f"{time.perf_counter() - start:.4f} seconds"
                # )

            return Response({"message": "OTP sent successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OtpVerifyView(APIView):
    @extend_schema(
        summary="Receive the code and verify it",
        description="استلام الكود والتحقق من صحته لتفعيل الحساب وسماح بالدخول ",
        request=VerifyOtpSerializer,
        responses={
            200:inline_serializer(
            name="AccountVerificationResponse",
            fields={
                "message":"Account verified successfully",
                "access":serializers.CharField(),
                "refresh":serializers.CharField(),
                "user":UserSerializer
                }
            ),
            400:OpenApiResponse(description="Invalid OTP")
        }
    )
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            try:
                otp = Otp.objects.get(user__email=email, otp_code=otp_code)
                if otp.is_expired():
                    return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST) 
                user = otp.user
                user.status = True
                user.save()
                otp.delete()
                refresh=RefreshToken.for_user(user)
                return Response({"message":"Account verified successfully",
                          "access":str(refresh.access_token),
                          "refresh":str(refresh),
                          "user":UserSerializer(user).data},  # بيانات المستخدم كامل
                           status=status.HTTP_200_OK)                 
            except Otp.DoesNotExist:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OtpResendView(APIView):
    @extend_schema(
        summary="Resend OTP code ",
        description="اعادة ارسال كود التحقق",
        request=inline_serializer(
            name="OtpResendRequest",
            fields={
                "email":serializers.EmailField()
            }
        ),
        responses={
            200:OpenApiResponse(description="OTP code resent successfully."),
            400:OpenApiResponse(description="User with this email does not exist")
        }
    )
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            with transaction.atomic():
                Otp.objects.filter(user=user).delete()  # Delete any existing OTPs for the user
                code = generate_otp()
                Otp.objects.create(user=user, otp_code=code,
                                   expires_at=timezone.now() + timezone.timedelta(minutes=5))
                user_email=user.email
                send_to_email_task.delay(user_email,code)
            return Response({"message": "OTP code resent successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_400_BAD_REQUEST)

class LocalLoginView(APIView):
    @extend_schema(
        summary="Local Login",
        description="تسجيل الدخول باستخدام البريد الإلكتروني وكلمة المرور",
        request=LocalLoginSerializer,
        responses={
            200:inline_serializer(
            name="LocalLoginResponse",
            fields={
                "message":"Login successful",
                "access":serializers.CharField(),
                "refresh":serializers.CharField(),
                "user":UserSerializer
                }
            ),
            400: OpenApiResponse(description="Invalid credentials or unverified email")
        }
    )
    def post(self, request):
        serializer = LocalLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
                if not user.status:
                    return Response({"error": "Account exists but email is not verified"}, status=status.HTTP_400_BAD_REQUEST)
                refresh=RefreshToken.for_user(user)
                return Response({
                                "message": "Login successful",
                                "access": str(refresh.access_token),
                                "refresh": str(refresh),
                                "user": UserSerializer(user).data,   # بيانات المستخدم كاملة
                                }, status=status.HTTP_200_OK)           
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist"}, status=status.HTTP_400_BAD_REQUEST)

class GoogleAuthView(APIView):
    @extend_schema(
        summary="Google Authentication",
        description="تسجيل الدخول او انشاء حساب باستخدام  Google",
        request=GoogleAuthSerializer,
        responses={
            200:inline_serializer(
            name="GoogleLoginOrRegisterResponse",
            fields={
                "message":"Login successful",
                "access":serializers.CharField(),
                "refresh":serializers.CharField(),
                "user":UserSerializer
                }
            ),
            400: OpenApiResponse(description="Invalid Google token or unverified email")
        }
    )
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            idinfo = get_google_user_info(serializer.validated_data['access_token'])
        except ValueError:
            return Response({"error": "Invalid Google token"},
                            status=status.HTTP_400_BAD_REQUEST)

        google_sub = idinfo['sub']         
        email = idinfo.get('email')

        if not idinfo.get('email_verified'):
            return Response({"error": "Google email not verified"},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()

        if user:
            # المستخدم موجود مسبقاً → تسجيل دخول
            if user.auth_provider != User.AuthProvider.GOOGLE:
                return Response(
                    {"error": "This email is registered with a different method"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not user.provider_user_id:
                user.provider_user_id = google_sub
                user.save(update_fields=['provider_user_id'])
        else:
            user = User(
                full_name=idinfo.get('name', ''),
                email=email,
                provider_user_id=google_sub,
                auth_provider=User.AuthProvider.GOOGLE,
                status=True,
            )
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,   # بيانات المستخدم كاملة
        }, status=status.HTTP_200_OK)
        
class CompleteGoogleProfileView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="Complete Account Profile for Google Users",
        description="اكمال بيانات الحساب للمستخدمين الذين انشأوا حساب عبر Google",
        request=CompleteGoogleProfileSerializer,
        responses={200:OpenApiResponse(description="Profile completed successfully")}
    )
    def patch(self, request):
        serializer = CompleteGoogleProfileSerializer(
            instance=request.user,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {"message": "Profile completed successfully."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    @extend_schema(
        summary="Confirm Password Reset",
        description="تأكيد إعادة تعيين كلمة المرور",
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successful"),
            400: OpenApiResponse(description="Invalid OTP or user not found")
        }
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']

        otp= Otp.objects.filter(user__email=email, otp_code=otp_code).first()
        if otp is None:
            return Response({"error": "OTP expired or not found"},
                            status=status.HTTP_400_BAD_REQUEST)
        if otp.otp_code != otp_code:
            return Response({"error": "Invalid OTP"},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()
        otp.delete()      # الكود يُستخدم مرة واحدة فقط
        return Response({"message": "Password reset successful"},
                        status=status.HTTP_200_OK)

class SettingView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="Update Password",
        description="تحديث كلمة المرور",
        request=PasswordResetInSettingSerializer,
        responses={
            200: OpenApiResponse(description="Password updated successfully"),
            400: OpenApiResponse(description="Invalid current password")
        }
    )
    def patch(self,request):
        serializer=PasswordResetInSettingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_password=serializer.validated_data['current_password']
        new_password=serializer.validated_data['new_password']
        user=request.user
        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect"},
                            status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password updated successfully"},
                                status=status.HTTP_200_OK)
