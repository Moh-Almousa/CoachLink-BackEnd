import os
from celery import Celery

#لما تشتغل مع Django، استخدم ملف الإعدادات تبعي 
os.environ.setdefault('DJANGO_SETTINGS_MODULE','CoachLink.settings')

# هون أنشأنا Celery Application.
celery_app= Celery('CoachLink')
# جيب إعداداتك من Django settings. (CELERY_BROKER_URL)
celery_app.config_from_object('django.conf:settings',namespace='CELERY') #يعني Celery يهتم بالإعدادات الموجودة في Django والتي تبدأ بـ:
# روح دور لحالك على ملفات tasks.py الموجودة داخل Django apps.
celery_app.autodiscover_tasks()
