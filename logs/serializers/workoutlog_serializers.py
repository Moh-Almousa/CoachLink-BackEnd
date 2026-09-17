from rest_framework import serializers
from ..models import WorkoutLog,WorkoutSetLog

class WorkoutSetLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=WorkoutSetLog
        fields=['id','set_number','reps','weight']

class WorkoutLogSerializer(serializers.ModelSerializer):
    set_logs=WorkoutSetLogSerializer(many=True,read_only=True)
    class Meta:
        model=WorkoutLog
        fields=['id','program_day_exercise','note','status',
                'date_day','set_logs']
