from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

def notify(user,task,message,channels=('app',)):
    for channel in channels:
        Notification.objects.create(
            user=user, notification_task=task,
            transmission_channel=channel,
            message=message
        )
    if 'email' in channels and user.email:
        send_mail(
            subject=task,message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],fail_silently=True
        )
