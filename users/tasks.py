from celery import shared_task
from .utils import send_otp_email
import time
@shared_task
def send_to_email_task(email,code):
    print(" task send email start")
    send_otp_email(email=email,otp=code)
    print(" task send email finish")