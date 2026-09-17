"""
ASGI config for CoachLink project.
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoachLink.settings')

import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from chats.middleware import JWTAuthMiddlewareStack
from chats.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
