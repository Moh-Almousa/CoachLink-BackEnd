# مسارات WebSocket لتطبيق الشات - مقابل urls.py لكن لاتصالات WebSocket
from django.urls import re_path

from .consumers import ChatConsumer

websocket_urlpatterns = [
    # مثال: ws://localhost:8000/ws/chat/5/  -> conversation_id = 5
    re_path(r'ws/chat/(?P<conversation_id>\d+)/$', ChatConsumer.as_asgi()),
]
