from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import SubscriptionPlayer
from notifications.models import Notification
from notifications.utils import notify

class Command(BaseCommand):
    help = "بيبعت تذكير لكل لاعب اشتراكو رح يخلص خلال 3 أيام - لازم يتجدول يشتغل يومياً"

    def handle(self, *args, **options):
        now = timezone.now()
        expiring_subs = SubscriptionPlayer.objects.filter(
            status=SubscriptionPlayer.Status.ACTIVE,
            end_date__gte=now, end_date__lte=now + timedelta(days=3),
        ).select_related('player__user')

        for sub in expiring_subs:
            already_sent_today = Notification.objects.filter(
                user=sub.player.user,
                notification_task=Notification.Task.SUBSCRIPTION_REMINDER,
                created_at__date=now.date(),
            ).exists()
            if already_sent_today:
                continue
            notify(sub.player.user, Notification.Task.SUBSCRIPTION_REMINDER,
                   "Your subscription is about to expire soon. Renew now!",
                   channels=('app', 'email'))