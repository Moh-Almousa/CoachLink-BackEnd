from django.urls import path
from .views import ConversationListView,ConversationMessagesView,SendMessageView

urlpatterns = [
    # GET: list the user's conversations
    path('conversations/', ConversationListView.as_view(), name='chat-conversations'),

    # GET: messages of a conversation (marks them as read)
    path('conversations/<int:pk>/messages/', ConversationMessagesView.as_view(), name='chat-messages'),

    # POST (multipart/form-data): send a message
    path('messages/', SendMessageView.as_view(), name='chat-send-message'),
]