# urls.py for nutritions app
from django.urls import path
from .views import CoachCreateNutritionPlanView, FoodSearchView,CoachEidteNutritionPlanView

urlpatterns = [
    path('create/', CoachCreateNutritionPlanView.as_view(), name='coach-create-nutrition-plan'),
    path('foods/', FoodSearchView.as_view(), name='food-search'),
    path('player/<int:pk>/plan/',CoachEidteNutritionPlanView.as_view(),name='coach-eidte-nutition-plan'),
]
