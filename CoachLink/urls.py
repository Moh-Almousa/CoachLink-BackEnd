"""
URL configuration for CoachLink project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path , include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'),name='swagger-ui' ),
        #auth
    path('api/auth/', include('users.urls.auth_urls')),
    #coach
    path('api/coach/', include('users.urls.coach_urls')),
    #admin
    path('api/admin/', include('users.urls.admin_urls')),
    #player
    path('api/player/', include('users.urls.player_urls')),
    #subscriptions
    path('api/subscriptions/', include('subscriptions.urls')),
    #progarms
    path('api/programs/', include('programs.urls')),
    #nutritions
    path('api/nutritions/',include('nutritions.urls')),
    #logs
    path('api/nutritions-log/',include('logs.urls.nutritionlog_urls')),
    path('api/workout-log/',include('logs.urls.workoutlog_urls')),
    path('api/health-log/',include('logs.urls.health_urls')),
    #chat
    path('api/chat/',include('chats.urls')),
    #notifications
    path('api/notifications/',include('notifications.urls')),
    
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
