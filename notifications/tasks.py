# Celery tasks for the notifications app

from celery import shared_task
from django.core.management import call_command


# Send subscription expiry reminders (runs daily via celery beat)
@shared_task
def send_expiry_reminders_task():
    call_command('send_expiry_reminders')
