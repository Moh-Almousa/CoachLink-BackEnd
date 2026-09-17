from django.urls import path
from ..views.nutritionlog_views import (LogMealCompletionView,NutritionProfileView)

urlpatterns = [
    path('meal/',LogMealCompletionView.as_view(),name='log-meal'),
    path('nutrition-tap/<int:pk>/',NutritionProfileView.as_view(),name='Nutrition-Profile')
]