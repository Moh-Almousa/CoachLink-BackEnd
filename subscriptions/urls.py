from django.urls import path
from .views import SubscriptionPackageView, CreatePaymentAPIView, stripe_webhook
urlpatterns=[
    # Subscription Package Endpoints
    #4242424242424242
    path('packages/', SubscriptionPackageView.as_view(), name='subscription-packages'),
    path('packages/<int:pk>/', SubscriptionPackageView.as_view(), name='subscription-package-detail'),
    path("create/",CreatePaymentAPIView.as_view(),name="create-payment"),
    path("webhook/",stripe_webhook,name="stripe-webhook"),
]