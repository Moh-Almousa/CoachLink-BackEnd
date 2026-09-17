from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from ..views.auth_views import (LocalRegisterView,OtpVerifyView,OtpResendView,LocalLoginView,
                                GoogleAuthView,PasswordResetConfirmView,CompleteGoogleProfileView,
                                SettingView)

urlpatterns=[
    # مصادقة غوغل (إنشاء + دخول)
        path('google/', GoogleAuthView.as_view(), name='google-auth'),
        path('google/complete-profile/', CompleteGoogleProfileView.as_view(), name='complete-google-profile'),
        # تسجيل دخول محلي (إنشاء + دخول)
        path('local/register/', LocalRegisterView.as_view(), name='local-register'),
        path('local/login/', LocalLoginView.as_view(), name='local-login'),
        # التحقق من OTP
        path('otp/verify/', OtpVerifyView.as_view(), name='otp-verify'),
        path('otp/resend/', OtpResendView.as_view(), name='otp-resend'),
        # تحديث التوكن
        path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
        
        # نسيت كلمة السر
        path('password-reset/confirm/',
             PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

        path('setting/password-reset/',SettingView.as_view(),name='setting-rest-password'),
        
]
