from django.utils import timezone
from django.db import models
from django.db.models import Q
from users.models import CoachProfile, PlayerProfile

# Create your models here.
class SubscriptionPackage(models.Model):
    coach = models.ForeignKey(
        CoachProfile, on_delete=models.CASCADE, db_column='coach_id',
        related_name='packages'
    )
    number_month = models.IntegerField()
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(
        default=timezone.now, null=True, blank=True, db_column='creat_at'
    )

    class Meta:
        db_table = 'Subscription_Packages'


class Payment(models.Model):
    class Provider(models.TextChoices):
        STRIPE = 'stripe', 'Stripe'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    player = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, db_column='player_id',
        related_name='payments'
    )
    coach = models.ForeignKey(
        CoachProfile, on_delete=models.PROTECT, db_column='coach_id',
        related_name='payments'
    )
    package = models.ForeignKey(
        SubscriptionPackage, on_delete=models.PROTECT, db_column='package_id',
        related_name='payments'
    )
    platform_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=15, null=True, blank=True
    )
    platform_profit = models.DecimalField(max_digits=10, decimal_places=2)
    coach_profit = models.DecimalField(max_digits=10, decimal_places=2)
    payment_provider = models.CharField(
        max_length=50, choices=Provider.choices,
        default=Provider.STRIPE, null=True, blank=True
    )
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(
        max_length=50, choices=Status.choices,
        default=Status.PENDING, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        db_table = 'Payments'


class SubscriptionPlayer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        FINISH = 'finish', 'Finish'

    package = models.ForeignKey(
        SubscriptionPackage, on_delete=models.PROTECT, null=True, blank=True,
        db_column='package_id', related_name='subscriptions'
    )
    player = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, db_column='player_id',
        related_name='subscriptions'
    )
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, db_column='payments_id',
        related_name='subscriptions'
    )
    start_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(
        default=timezone.now, null=True, blank=True, db_column='creat_at'
    )

    class Meta:
        db_table = 'Subscription_Player'
        constraints = [
            models.UniqueConstraint(
                fields=['player'],
                condition=Q(status='active'),
                name='unique_active_subscription_per_player',
            )
        ]
