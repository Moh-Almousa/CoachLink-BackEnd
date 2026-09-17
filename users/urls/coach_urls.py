from django.urls import path
from ..views.coach_views import (CoachCertificateView,CoachProfileView,
                                CoachTransformationView,CoachListView,
                                CoachDetailView,PlayerInvitationView,
                                CoachDashboardView,CoachMyPlayers)

urlpatterns = [
    path('certificates/', CoachCertificateView.as_view(), name='coach-certificates'),
    path('profile/',       CoachProfileView.as_view(),     name='coach-profile'),
    path('transformations/', CoachTransformationView.as_view(), name='coach-transformations'),
    path('transformations/<int:pk>/', CoachTransformationView.as_view(), name='coach-transformation-detail'),
    path('cards/', CoachListView.as_view(), name='coach-cards'),
    path('<int:pk>/',CoachDetailView.as_view(),name='coach-detail'),
    path('invite-player/', PlayerInvitationView.as_view(), name='coach-invite-player'),
    path('dashboard/', CoachDashboardView.as_view(), name='coach-dashboard'),
    path('my-players/', CoachMyPlayers.as_view(), name='coach-my-players'),

]