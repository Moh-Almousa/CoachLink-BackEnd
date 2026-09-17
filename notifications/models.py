from django.utils import timezone

from django.db import models

from users.models import User

# Create your models here.
class Notification(models.Model):
    class Task(models.TextChoices):
        SUBSCRIPTION_REMINDER = 'Subscription reminder', 'Subscription reminder'
        CERT_ACCEPTED = 'Acceptance of certificate', 'Acceptance of certificate'
        CERT_REFUSED = 'Refusal of certificate', 'Refusal of certificate'
        OTHER = 'other', 'Other'

    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        APP = 'app', 'App'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, db_column='user_id',
        related_name='notifications'
    )
    notification_task = models.CharField(
        max_length=50, choices=Task.choices, null=True, blank=True
    )
    transmission_channel = models.CharField(
        max_length=50, choices=Channel.choices, null=True, blank=True
    )
    message = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(
        default=timezone.now, null=True, blank=True, db_column='create_at'
    )

    class Meta:
        db_table = 'Notifications'
