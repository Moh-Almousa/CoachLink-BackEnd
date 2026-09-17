# serializers.py for nutritions app
from decimal import Decimal

from rest_framework import serializers

from users.models import PlayerProfile
from .models import NutritionPlan, NutritionPlanWeek, NutritionPlanDay, NutritionPlanMeal, MealFood


# ============ سيريالايزرز الإدخال (التحقق من بيانات إنشاء الخطة) ============

class MealFoodInputSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=100, source='api_id_food')
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    size = serializers.CharField(max_length=50, source='quantity')
    kcal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, source='calories')
    protein = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)
    carb = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, source='carbs')
    fat = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)
    fiber = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, required=False, default=Decimal('0'))

class NutritionPlanMealInputSerializer(serializers.Serializer):
    meal_number = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    # وجبة بدون أطعمة = لسا ماتعبّت (نفس فكرة يوم الراحة بالبرنامج الرياضي)
    foods = MealFoodInputSerializer(many=True, required=False, default=list)

class NutritionPlanDayInputSerializer(serializers.Serializer):
    number_day = serializers.IntegerField(min_value=1, max_value=7)
    meals = NutritionPlanMealInputSerializer(many=True)

    def validate_meals(self, value):
        if not value:
            raise serializers.ValidationError("Each day must contain at least one meal.")
        meal_numbers = [meal['meal_number'] for meal in value]
        if sorted(meal_numbers) != list(range(1, len(value) + 1)):
            raise serializers.ValidationError("Meals must be numbered sequentially starting from 1.")
        return value

class NutritionPlanWeekInputSerializer(serializers.Serializer):
    number_week = serializers.IntegerField(min_value=1)
    days = NutritionPlanDayInputSerializer(many=True)

    def validate_days(self, value):
        day_numbers = [day['number_day'] for day in value]
        if sorted(day_numbers) != list(range(1, 8)):
            raise serializers.ValidationError("Each week must contain exactly 7 days, numbered 1 to 7.")
        return value

class CreateNutritionPlanSerializer(serializers.Serializer):
    playerId = serializers.PrimaryKeyRelatedField(queryset=PlayerProfile.objects.all(), source='player')
    name = serializers.CharField(max_length=100)
    number_of_months = serializers.IntegerField(min_value=1, max_value=12)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    weeks = NutritionPlanWeekInputSerializer(many=True)

    def validate_weeks(self, value):
        if not value:
            raise serializers.ValidationError("Program must contain at least one week.")
        week_numbers = [week['number_week'] for week in value]
        if sorted(week_numbers) != list(range(1, len(value) + 1)):
            raise serializers.ValidationError("Weeks must be numbered sequentially starting from 1.")
        return value


# ============ سيريالايزرز التعديل (إضافة/حذف وجبة أو طعام على خطة موجودة) ============

class UpdateMealFoodInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    food_id = serializers.CharField(max_length=100, source='api_id_food')
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    size = serializers.CharField(max_length=50, source='quantity')
    kcal = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, source='calories')
    protein = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)
    carb = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, source='carbs')
    fat = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)
    fiber = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, required=False, default=Decimal('0'))

class UpdateNutritionPlanMealInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    meal_number = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    foods = UpdateMealFoodInputSerializer(many=True, required=False, default=list)

class UpdateNutritionPlanDayInputSerializer(serializers.Serializer):
    number_day = serializers.IntegerField(min_value=1, max_value=7)
    # عدد الوجبات مفتوح - يمكن تكون أقل أو أكثر من الأصل (وجبة محذوفة/مضافة)
    meals = UpdateNutritionPlanMealInputSerializer(many=True, required=False, default=list)

    def validate_meals(self, value):
        meal_numbers = [meal['meal_number'] for meal in value]
        if len(set(meal_numbers)) != len(meal_numbers):
            raise serializers.ValidationError("Each meal in a day must have a unique meal_number.")
        return value

class UpdateNutritionPlanWeekInputSerializer(serializers.Serializer):
    number_week = serializers.IntegerField(min_value=1)
    days = UpdateNutritionPlanDayInputSerializer(many=True)

    def validate_days(self, value):
        day_numbers = [day['number_day'] for day in value]
        if sorted(day_numbers) != list(range(1, 8)):
            raise serializers.ValidationError("Each week must contain exactly 7 days, numbered 1 to 7.")
        return value

class UpdatePlanSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    weeks = UpdateNutritionPlanWeekInputSerializer(many=True, required=False)

    def validate_weeks(self, value):
        if not value:
            raise serializers.ValidationError("Program must contain at least one week.")
        week_numbers = [week['number_week'] for week in value]
        if sorted(week_numbers) != list(range(1, len(value) + 1)):
            raise serializers.ValidationError("Weeks must be numbered sequentially starting from 1.")
        return value


# ============ سيريالايزرز العرض (إرجاع الخطة بعد إنشائها) ============

class MealFoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealFood
        fields = ['id', 'api_id_food', 'name', 'quantity', 'calories', 'protein', 'carbs', 'fat', 'fiber']

class NutritionPlanMealSerializer(serializers.ModelSerializer):
    foods = MealFoodSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlanMeal
        fields = ['id', 'meal_number', 'name', 'foods']

class NutritionPlanDaySerializer(serializers.ModelSerializer):
    meals = NutritionPlanMealSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlanDay
        fields = ['id', 'number_day', 'name_day', 'meals']

class NutritionPlanWeekSerializer(serializers.ModelSerializer):
    days = NutritionPlanDaySerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlanWeek
        fields = ['id', 'number_week', 'days']

class NutritionPlanSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.user.full_name', read_only=True)
    weeks = NutritionPlanWeekSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlan
        fields = ['id', 'player', 'player_name', 'name', 'note', 'start_at', 'end_at',
                  'calories_target', 'protein_target', 'carbs_target', 'fat_target', 'fiber_target',
                  'is_active', 'created_at', 'weeks']

# ============ سيريالايزرز GET خاصة بشاشة تعديل الكوتش (CoachEidteNutritionPlanView.get) ============

class MealFoodEditSerializer(serializers.ModelSerializer):
    food_id = serializers.CharField(source='api_id_food')
    size = serializers.CharField(source='quantity')
    kcal = serializers.DecimalField(max_digits=18, decimal_places=2, source='calories')
    carb = serializers.DecimalField(max_digits=18, decimal_places=2, source='carbs')

    class Meta:
        model = MealFood
        fields = ['id', 'food_id', 'name', 'size', 'kcal', 'protein', 'carb', 'fat', 'fiber']

class NutritionPlanMealEditSerializer(serializers.ModelSerializer):
    foods = MealFoodEditSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlanMeal
        fields = ['id', 'meal_number', 'name', 'foods']

class NutritionPlanDayEditSerializer(serializers.ModelSerializer):
    meals = NutritionPlanMealEditSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlanDay
        fields = ['number_day', 'meals']

class NutritionPlanWeekEditSerializer(serializers.ModelSerializer):
    days = NutritionPlanDayEditSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlanWeek
        fields = ['number_week', 'days']

class NutritionPlanEditSerializer(serializers.ModelSerializer):
    weeks = NutritionPlanWeekEditSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionPlan
        fields = ['name', 'note', 'weeks']
