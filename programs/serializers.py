# serializers.py for programs app
from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from users.models import PlayerProfile
from .models import ProgramPlanExercise, ProgramWeek, ProgramDay, ProgramDayExercise


# ============ سيريالايزرز الإدخال (التحقق من بيانات إنشاء البرنامج) ============

class ProgramDayExerciseInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    api_id_exercise = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=100)
    sets = serializers.IntegerField(min_value=1)
    reps = serializers.IntegerField(min_value=1)
    # الفرونت بيبعت الوزن كنص فيه وحدة (مثلاً "20 kg")، مش رقم صافي
    weight = serializers.CharField()
    youtubeLink = serializers.CharField(max_length=255, required=False, allow_blank=True,
                                         allow_null=True, source='video_url')

    def validate_weight(self, value):
        cleaned = str(value).lower().replace('kg', '').strip()
        try:
            weight = Decimal(cleaned)
        except InvalidOperation:
            raise serializers.ValidationError("Weight must be a valid number, e.g. '20' or '20 kg'.")
        if weight < 0:
            raise serializers.ValidationError("Weight must be 0 or greater.")
        return weight

class ProgramDayInputSerializer(serializers.Serializer):
    number_day = serializers.IntegerField(min_value=1, max_value=7)
    # يوم بدون تمارين = يوم راحة (ما بننشئلو أي صف ProgramDayExercise)
    exercises = ProgramDayExerciseInputSerializer(many=True, required=False, default=list)

class ProgramWeekInputSerializer(serializers.Serializer):
    number_week = serializers.IntegerField(min_value=1)
    days = ProgramDayInputSerializer(many=True)

    def validate_days(self, value):
        day_numbers = [day['number_day'] for day in value]
        if sorted(day_numbers) != list(range(1, 8)):
            raise serializers.ValidationError("Each week must contain exactly 7 days, numbered 1 to 7.")
        return value

class CreateProgramSerializer(serializers.Serializer):
    playerId = serializers.PrimaryKeyRelatedField(queryset=PlayerProfile.objects.all(), source='player')
    name = serializers.CharField(max_length=100)
    number_of_months = serializers.IntegerField(min_value=1, max_value=12)
    weeks = ProgramWeekInputSerializer(many=True)

    def validate_weeks(self, value):
        if not value:
            raise serializers.ValidationError("Program must contain at least one week.")
        week_numbers = [week['number_week'] for week in value]
        if sorted(week_numbers) != list(range(1, len(value) + 1)):
            raise serializers.ValidationError("Weeks must be numbered sequentially starting from 1.")
        return value

# سيرلايزر التعديل
class UpdateProgramSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100,required=False)
    weeks = ProgramWeekInputSerializer(many=True,required=False)

    def validate_weeks(self, value):
        if not value:
            raise serializers.ValidationError( "Program must contain at least one week.")
        week_numbers = [week['number_week'] for week in value]
        if sorted(week_numbers) != list( range(1, len(value) + 1)):
            raise serializers.ValidationError("Weeks must be numbered sequentially starting from 1.")
        return value


# ============ سيريالايزرز العرض (إرجاع البرنامج بعد إنشائه) ============

class ProgramDayExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramDayExercise
        fields = ['id', 'api_id_exercise', 'name', 'video_url', 'weight', 'sets', 'reps']

class ProgramDaySerializer(serializers.ModelSerializer):
    exercises = ProgramDayExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = ProgramDay
        fields = ['id', 'number_day', 'name_day', 'exercises']

class ProgramWeekSerializer(serializers.ModelSerializer):
    days = ProgramDaySerializer(many=True, read_only=True)

    class Meta:
        model = ProgramWeek
        fields = ['id', 'number_week', 'days']

class ProgramPlanSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.user.full_name', read_only=True)
    weeks = ProgramWeekSerializer(many=True, read_only=True)

    class Meta:
        model = ProgramPlanExercise
        fields = ['id', 'player', 'player_name', 'name', 'start_at', 'end_at', 'created_at', 'weeks']


#  سيريالايزرز GET خاصة بشاشة تعديل الكوتش 

class ProgramDayExerciseEditSerializer(serializers.ModelSerializer):
    youtubeLink = serializers.CharField(source='video_url')

    class Meta:
        model = ProgramDayExercise
        fields = ['id', 'api_id_exercise', 'name', 'sets', 'reps', 'weight', 'youtubeLink']

class ProgramDayEditSerializer(serializers.ModelSerializer):
    exercises = ProgramDayExerciseEditSerializer(many=True, read_only=True)

    class Meta:
        model = ProgramDay
        fields = ['number_day', 'exercises']

class ProgramWeekEditSerializer(serializers.ModelSerializer):
    days = ProgramDayEditSerializer(many=True, read_only=True)

    class Meta:
        model = ProgramWeek
        fields = ['number_week', 'days']

class ProgramPlanEditSerializer(serializers.ModelSerializer):
    weeks = ProgramWeekEditSerializer(many=True, read_only=True)

    class Meta:
        model = ProgramPlanExercise
        fields = ['name', 'weeks']
