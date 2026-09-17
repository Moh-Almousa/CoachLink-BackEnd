import random
import requests

from django.conf import settings
from django.core.mail import send_mail


def get_google_user_info(access_token):
    """يتحقق من access_token تبع غوغل بمناداة Google userinfo API مباشرة،
    ويرجّع بيانات المستخدم (dict) أو يرمي ValueError إذا كان التوكن غير صالح."""
    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code != 200:
        raise ValueError("Invalid Google access token")
    # الرد بيحتوي: sub, email, email_verified, name, given_name, family_name, picture
    return response.json()


def generate_otp():
    return f'{random.randint(100000, 999999)}'


def send_otp_email(email, otp):
    send_mail(
        subject='رمز التحقق',
        message=f'رمز التحقق الخاص بك هو: {otp}\nصالح لمدة 5 دقائق.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )