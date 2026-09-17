from rest_framework import serializers
from ..models import DailyPhysicalHealth,BodyMeasurement

class DailyPhysicalHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model=DailyPhysicalHealth
        fields=['id','weight_kg','date_day']
        
class BodyMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model=BodyMeasurement
        fields=['id','muscle_name','value_cm','date_day']
    