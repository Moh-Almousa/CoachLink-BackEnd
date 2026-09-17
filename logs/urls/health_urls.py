from django.urls import path
from ..views.health_views import LogWeightView,WeightProfileView,LogBodyMeasurementsView,BodyMeasurementsProfileView

urlpatterns = [
    path('weight-log/',LogWeightView.as_view(),name='weight-log'),
    path('weight-tap/<int:pk>/',WeightProfileView.as_view(),name='weight-profile'),

    path('measurements-log/',LogBodyMeasurementsView.as_view(),name='body-measure-log'),
    path('measurements-tap/<int:pk>/',BodyMeasurementsProfileView.as_view(),name='body-measure-profile')
]