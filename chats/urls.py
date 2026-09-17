from django.urls import path
from .views import ConversationListView,ConversationMessagesView,SendMessageView

urlpatterns = [
    # GET - بدون body
    # Response: [
    #   {
    #     "id": 5,
    #     "other_user": {"id": 12, "name": "Omar Khaled", "image": "/media/... أو null"},
    #     "is_active": true,
    #     "last_message": {"preview": "hello" أو "Attachment", "sent_at": "2026-08-16T09:00:00Z", "has_attachment": false} أو null,
    #     "updated_at": "2026-08-16T09:00:00Z"
    #   }, ...
    # ]  (مرتبة الأحدث أولاً حسب last_message.sent_at)
    path('conversations/', ConversationListView.as_view(), name='chat-conversations'),

    # GET - بدون body، pk = ChatConversation.id
    # نداء واحد بس لفتح شات: بيجيب الرسائل وبنفس الوقت بيعلّم كل رسائل الطرف
    # التاني (sent/delivered) كـ read - ما في داعي لنداء منفصل لتعليم القراءة.
    # Response: [
    #   {
    #     "id": 101, "chat": 5, "sent_by": 12, "content": "hello",
    #     "attachment": "http://.../media/chat_attachments/x.png" أو null,
    #     "attachment_type": "image" | "video" | "file" أو null,
    #     "status": "sent" | "delivered" | "read", "sent_at": "2026-08-16T09:00:00Z"
    #   }, ...
    # ]  (مرتبة زمنياً من الأقدم للأحدث)
    path('conversations/<int:pk>/messages/', ConversationMessagesView.as_view(), name='chat-messages'),

    # POST - multipart/form-data (لازم multipart مش JSON عشان attachment ملف)
    # Request:
    #   receiver_id: 12          (إجباري - User.id تبع الطرف التاني)
    #   content: "hello"          (اختياري)
    #   attachment: <file>        (اختياري)
    #   attachment_type: "image" | "video" | "file"   (اختياري - مطلوب لو في attachment)
    #   * لازم content أو attachment موجود، مش الاثنين فاضيين
    # Response (201): نفس شكل عنصر واحد من قائمة messages فوق
    # أخطاء ممكنة: 400 (content وattachment فاضيين سوا)،
    #             404 (receiver_id مش موجود)، 403 (الاشتراك مش نشط حالياً)
    path('messages/', SendMessageView.as_view(), name='chat-send-message'),
]