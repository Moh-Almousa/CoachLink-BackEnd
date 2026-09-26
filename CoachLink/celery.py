import os
from celery import Celery

#لما تشتغل مع Django، استخدم ملف الإعدادات تبعي 
os.environ.setdefault('DJANGO_SETTINGS_MODULE','CoachLink.settings')

# هون أنشأنا Celery Application.
celery_app= Celery('CoachLink')
# جيب إعداداتك من Django settings. (CELERY_BROKER_URL)
celery_app.config_from_object('django.conf:settings',namespace='CELERY') #يعني Celery يهتم بالإعدادات الموجودة في Django والتي تبدأ بـ:
# ويندوز ما بيدعم الـ prefork pool: التاسكات بتوصل للـ worker وبتعلق بدون تنفيذ.
# solo بس عالويندوز (تشغيل محلي بدون دوكر)، ودوكر (لينكس) بيضل عالـ prefork.
if os.name == 'nt':
    celery_app.conf.worker_pool = 'solo'
# روح دور لحالك على ملفات tasks.py الموجودة داخل Django apps.
celery_app.autodiscover_tasks()
