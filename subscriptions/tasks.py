# tasks.py لتطبيق الاشتراكات - المهام يلي بينفذها الـ celery worker بالخلفية.
# الـ worker بيلاقي هالملف لحالو عن طريق autodiscover_tasks() بـ CoachLink/celery.py

from celery import shared_task
from django.utils import timezone

from .models import SubscriptionPlayer


# إنهاء الاشتراكات يلي خلص وقتها (end_date صار بالماضي): active -> finish
# celery beat بيشغّلها كل ساعة حسب CELERY_BEAT_SCHEDULE بـ settings.py
# ليش لازمة: الاشتراك ما بيتغير لـ finish لحالو، ومن دونها:
#   - اللاعب ما بيقدر يشترك من جديد (CreatePaymentAPIView بترفض أي حدا عندو اشتراك active)
#   - الشات بيضل مفتوح للأبد (has_active_subscription بتفحص الـ status بس)
@shared_task
def expire_subscriptions_task():
    # update() بتعمل استعلام UPDATE واحد لكل الاشتراكات سوا بدل ما نمر عليهن وحدة وحدة
    # (وما بتطلق post_save - ما في signal على الاشتراك بيحتاجها هون)
    expired_count = SubscriptionPlayer.objects.filter(
        status=SubscriptionPlayer.Status.ACTIVE,
        end_date__lt=timezone.now(),
    ).update(status=SubscriptionPlayer.Status.FINISH)

    # القيمة يلي بترجعها الـ task بتطلع بـ logs الـ worker: ... succeeded in 0.01s: 3
    return expired_count
