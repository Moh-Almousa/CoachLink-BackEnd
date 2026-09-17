from django.urls import path
from ..views.player_views import PlayerProfileOverviewView,PlayerFitnessProfileViews, PlayerDashboardView, PlayerRateCoachView
urlpatterns = [
    path('fitnes/',PlayerFitnessProfileViews.as_view(),name='player-fitness'),
    path('dashboard/',PlayerDashboardView.as_view(),name='player-dashboard'),
    path('rate-coach/',PlayerRateCoachView.as_view(),name='player-rate-coach'),
    path('profile-overview/<int:pk>/',PlayerProfileOverviewView.as_view(),name='player-profile-overview')
]