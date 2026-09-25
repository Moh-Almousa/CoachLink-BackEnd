# tasks.py لتطبيق الإشعارات - المهام يلي بينفذها الـ celery worker بالخلفية.
# الـ worker بيلاقي هالملف لحالو عن طريق autodiscover_tasks() بـ CoachLink/celery.py

from celery import shared_task
from django.core.management import call_command


# تذكير اللاعبين يلي اشتراكهن رح يخلص خلال 3 أيام.
# celery beat بيشغّلها كل يوم حسب CELERY_BEAT_SCHEDULE بـ settings.py
# ما نسخنا المنطق لهون - الـ task بتنادي نفس الـ command الموجود
# (notifications/management/commands/send_expiry_reminders.py)
# فالمنطق بمكان واحد، والـ command بيضل ينفع للتشغيل اليدوي:
#   python manage.py send_expiry_reminders
@shared_task
def send_expiry_reminders_task():
    call_command('send_expiry_reminders')
