from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from users.models import Certificate, AdminProfile
from subscriptions.models import SubscriptionPlayer
from chats.models import ChatMessage
from programs.models import ProgramPlanExercise
from nutritions.models import NutritionPlan

from .models import Notification
from .utils import notify

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from chats.serializers import ChatMessageSerializer


# --- بند 1 + 6: الشهادة (رفع جديد -> أدمن | تغيير حالة -> كوتش) ---
@receiver(pre_save, sender=Certificate)
def stash_old_certificate_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Certificate.objects.get(pk=instance.pk).verification_status
        except Certificate.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Certificate)
def notify_certificate_review(sender, instance, created, **kwargs):
    if created:
        # بند 6: شهادة جديدة اترفعت - إشعار كل الأدمنز (موقع + بريد)
        for admin in AdminProfile.objects.select_related('user').all():
            notify(admin.user, Notification.Task.OTHER,
                   f"New certificate uploaded by {instance.coach_profile.user.full_name} - needs review.",
                   channels=('app', 'email'))
        return

    old_status = getattr(instance, '_old_status', None)
    if old_status == instance.verification_status:
        return  # ما تغيرت الحالة فعلياً (save لسبب تاني)

    # بند 1: تغيرت الحالة - إشعار الكوتش بالبريد بس
    if instance.verification_status == Certificate.VerificationStatus.ACCEPTED:
        notify(instance.coach_profile.user, Notification.Task.CERT_ACCEPTED,
               "Your certificate has been verified and accepted.", channels=('email',))
    elif instance.verification_status == Certificate.VerificationStatus.REJECTED:
        notify(instance.coach_profile.user, Notification.Task.CERT_REFUSED,
               "Your certificate has been reviewed and rejected.", channels=('email',))


# --- بند 2: اشتراك لاعب جديد -> الكوتش (موقع + بريد) ---
@receiver(post_save, sender=SubscriptionPlayer)
def notify_new_subscription(sender, instance, created, **kwargs):
    if not created:
        return
    notify(instance.package.coach.user, Notification.Task.OTHER,
           f"{instance.player.user.full_name} just subscribed to your coaching plan.",
           channels=('app', 'email'))


# --- بند 4: رسالة جديدة -> الطرف التاني (موقع بس، متل واتساب) ---
@receiver(post_save, sender=ChatMessage)
def notify_new_message(sender, instance, created, **kwargs):
    if not created:
        return
    conversation = instance.chat
    receiver_user = (conversation.player.user if instance.sent_by == conversation.coach.user
                      else conversation.coach.user)
    notify(receiver_user, Notification.Task.OTHER,
           f"New message from {instance.sent_by.full_name}.", channels=('app',))

# --- بث لحظي عبر WebSocket لنفس الرسالة (بالإضافة للإشعار فوق) ---
@receiver(post_save, sender=ChatMessage)
def broadcast_new_message(sender, instance, created, **kwargs):
    if not created:
        return
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    message_data = ChatMessageSerializer(instance).data
    async_to_sync(channel_layer.group_send)(
        f'chat_{instance.chat_id}',
        {'type': 'chat_message', 'message': message_data}
    )


# --- بند 5: برنامج/خطة تغذية جديدة -> اللاعب (موقع + بريد) ---
@receiver(post_save, sender=ProgramPlanExercise)
def notify_new_program(sender, instance, created, **kwargs):
    if not created:
        return
    notify(instance.player.user, Notification.Task.OTHER,
           f"Your coach assigned you a new workout program: {instance.name}.",
           channels=('app', 'email'))

@receiver(post_save, sender=NutritionPlan)
def notify_new_nutrition_plan(sender, instance, created, **kwargs):
    if not created:
        return
    notify(instance.player.user, Notification.Task.OTHER,
           f"Your coach assigned you a new nutrition plan: {instance.name}.",
           channels=('app', 'email'))