from django.urls import path
from ..views.admin_views import CertificateAuthenticationView ,AdminDashboardView

urlpatterns = [
    path('certificates/',CertificateAuthenticationView.as_view(), name='admin-certificates-list'),
    path('certificates/review/',CertificateAuthenticationView.as_view(), name='admin-certificates-review'),
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
      
]