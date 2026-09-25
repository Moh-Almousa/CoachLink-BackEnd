# Celery tasks for the subscriptions app

from celery import shared_task
from django.utils import timezone

from .models import SubscriptionPlayer


# Mark subscriptions past their end date as finished (runs hourly via celery beat)
@shared_task
def expire_subscriptions_task():
    expired_count = SubscriptionPlayer.objects.filter(
        status=SubscriptionPlayer.Status.ACTIVE,
        end_date__lt=timezone.now(),
    ).update(status=SubscriptionPlayer.Status.FINISH)

    return expired_count
