from django.urls import path
from ..views.workoutlog_views import LogWorkoutView,WorkoutProfileView
urlpatterns = [
    path('workout-log/',LogWorkoutView.as_view(),name='Log-Workout'),
    path('workout-tap/<int:pk>/',WorkoutProfileView.as_view(),name='Workout-Profile')
]
