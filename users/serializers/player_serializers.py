from rest_framework import serializers
from ..models import PlayerProfile, User, CoachRating

class PlayerFitnessProfileSerializer(serializers.ModelSerializer):
    goal = serializers.ChoiceField(choices=PlayerProfile.Goal.choices, required=False)
    weight = serializers.DecimalField(source='weight_kg', max_digits=5, decimal_places=2, min_value=0, required=False)
    height = serializers.IntegerField(source='height_cm', min_value=0, required=False)
    trainingExperience= serializers.IntegerField(source='training_age_years', min_value=0, required=False)
    healthStatus = serializers.CharField(source='note_sick', required=False, allow_blank=True)
    hasInjuries= serializers.BooleanField(source='is_injury', required=False)
    injuryDetails= serializers.CharField(source='note_injury', required=False, allow_blank=True)
    class Meta:
        model= PlayerProfile
        fields= ['id','goal','weight','height','trainingExperience','healthStatus',
                 'hasInjuries','injuryDetails']

class PlayerDashboardSerializer(serializers.Serializer):
    player_profile_id = serializers.IntegerField(read_only=True)
    coach_name = serializers.CharField(read_only=True, allow_null=True)
    coach_image = serializers.CharField(read_only=True, allow_null=True)
    coach_id = serializers.IntegerField(read_only=True, allow_null=True)
    # Coach's User.id (used as receiver_id in chat)
    coach_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    package_name = serializers.CharField(read_only=True)
    days_left = serializers.IntegerField(read_only=True)
    target_kcal = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    consumed_kcal = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    latest_weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    weight_logs = serializers.ListField(read_only=True)

class RateCoachInputSerializer(serializers.Serializer):
    coachId = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)

class CoachRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachRating
        fields = ['id','coach','rating','created_at']

class PlayerProfileOverviewSerializer(serializers.Serializer):
    name=serializers.CharField(read_only=True)
    image=serializers.CharField(read_only=True,allow_null=True)
    bio=serializers.CharField(read_only=True,allow_null=True)
    coach_name = serializers.CharField(read_only=True, allow_null=True)
    plan_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True, allow_null=True)
    height_cm = serializers.IntegerField(read_only=True, allow_null=True)
    weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    weight_change_kg = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    training_age_years = serializers.IntegerField(read_only=True, allow_null=True)
    goal = serializers.CharField(read_only=True, allow_null=True)
    health_status = serializers.CharField(read_only=True, allow_null=True)
    has_injuries = serializers.BooleanField(read_only=True)
    injury_details = serializers.CharField(read_only=True, allow_null=True)
    active_workout_name = serializers.CharField(read_only=True, allow_null=True)
    total_weeks_count = serializers.IntegerField(read_only=True)
    completed_weeks_count = serializers.IntegerField(read_only=True)
    workout_progress_percent = serializers.IntegerField(read_only=True)
    active_nutrition_name = serializers.CharField(read_only=True, allow_null=True)
    active_nutrition_kcal = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    carbs_percent = serializers.IntegerField(read_only=True)
    protein_percent = serializers.IntegerField(read_only=True)
    fat_percent = serializers.IntegerField(read_only=True)
    
