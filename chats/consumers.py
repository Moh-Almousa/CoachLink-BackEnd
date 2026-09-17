# consumers.py لتطبيق الشات - Consumer واحد بسيط لكل محادثة.
# دوره الوحيد: ضم المستخدم لـ "غرفة" المحادثة وتوصيل الرسائل الجاهزة له
# لحظياً. الحفظ بقاعدة البيانات يضل بالكامل عن طريق SendMessageView (REST)
# - الاتجاه هون سيرفر->متصفح بس، ما في استقبال إرسال حقيقي من هون.

import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ChatConversation
from .views import is_conversation_participant


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self): # دالة الاتصال
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.group_name = f'chat_{self.conversation_id}'
        user = self.scope['user']

        if user.is_anonymous:
            await self.close()
            return

        allowed = await self.is_participant(user)
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code): #دالة الفصل
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None): # دالة الاستقبال من الفروند 
        # الإرسال يضل عن طريق REST (SendMessageView) بس - منتجاهل أي شي
        # يجي من هون عشان ما ينكسر الاتصال
        pass

    # بتنستدعى تلقائياً لما حدا يعمل group_send بـ type='chat_message'
    async def chat_message(self, event): # دالة استقبال داخلي تعتبر ربط المشروع مع ال web socket
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def is_participant(self, user):
        try:
            conversation = ChatConversation.objects.get(id=self.conversation_id)
        except ChatConversation.DoesNotExist:
            return False
        return is_conversation_participant(user, conversation)
