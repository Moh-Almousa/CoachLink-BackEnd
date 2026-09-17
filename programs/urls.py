# urls.py for programs app
from django.urls import path
from .views import CoachCreateProgramView, ExerciseSearchView,CoachEditeProgame

urlpatterns = [
    path('create/', CoachCreateProgramView.as_view(), name='coach-create-program'),
    path('exercises/', ExerciseSearchView.as_view(), name='exercise-search'),
    path('players/<int:pk>/program/', CoachEditeProgame.as_view(), name='coach-edit-program'),
]
