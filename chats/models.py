from django.utils import timezone

from django.db import models

from users.models import CoachProfile, PlayerProfile, User

# Create your models here.
class ChatConversation(models.Model):
    coach = models.ForeignKey(
        CoachProfile, on_delete=models.PROTECT, db_column='coach_id',
        related_name='conversations'
    )
    player = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, db_column='player_id',
        related_name='conversations'
    )
    created_at = models.DateTimeField(
        default=timezone.now, null=True, blank=True, db_column='create_at'
    )
    updated_at = models.DateTimeField(null=True, blank=True, db_column='update_at')

    class Meta:
        db_table = 'chat_conversation'
        constraints = [
            models.UniqueConstraint(
                fields=['coach', 'player'], name='uq_conversation_coach_player'
            )
        ]


class ChatMessage(models.Model):
    class AttachmentType(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'
        FILE = 'file', 'File'

    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        READ = 'read', 'Read'

    chat = models.ForeignKey(
        ChatConversation, on_delete=models.CASCADE, db_column='chat_id',
        related_name='messages'
    )
    sent_by = models.ForeignKey(
        User, on_delete=models.PROTECT, db_column='sent_by',
        related_name='sent_messages'
    )
    # اختياري - ممكن ترسل مرفق بدون نص (صورة/فيديو/ملف لحاله)
    content = models.TextField(blank=True)
    # مرفق عام (صورة/فيديو/أي ملف) بدل ImageField المحصورة بالصور بس
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    attachment_type = models.CharField(
        max_length=20, choices=AttachmentType.choices, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    #reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,db_column='reply_to_id', related_name='replies')
    sent_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        db_table = 'chat_messages'
