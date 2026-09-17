from rest_framework import serializers
from ..models import NutritionLog

class NutritionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=NutritionLog
        fields=['id','meal','status','date_day','calories_total',
                'protein','carbs','fat','fiber']
        extra_kwargs ={
            'calories_total':{'read_only': True},
            'protein':{'read_only': True},
            'carbs':{'read_only': True},
            'fat':{'read_only': True},
            'fiber':{'read_only': True},
        }

