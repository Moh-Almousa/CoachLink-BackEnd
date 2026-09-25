from django.utils import timezone

from django.core.validators import MinValueValidator
from django.db import models

from users.models import CoachProfile, PlayerProfile

# Create your models here.
class NutritionPlan(models.Model):
    coach = models.ForeignKey(
        CoachProfile, on_delete=models.PROTECT, db_column='coach_id',
        related_name='nutrition_plans'
    )
    player = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, db_column='player_id',
        related_name='nutrition_plans'
    )
    name = models.CharField(max_length=100)
    start_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    end_at = models.DateTimeField()
    note = models.CharField(max_length=500, null=True, blank=True)
    calories_target = models.DecimalField(max_digits=18, decimal_places=2)
    protein_target = models.DecimalField(max_digits=18, decimal_places=2)
    carbs_target = models.DecimalField(max_digits=18, decimal_places=2)
    fat_target = models.DecimalField(max_digits=18, decimal_places=2)
    fiber_target = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(
        default=timezone.now, null=True, blank=True, db_column='creat_at'
    )
    updated_at = models.DateField(auto_now=True)

    class Meta:
        db_table = 'Nutrition_plans'

    # Current day number in the plan (1-based), based on elapsed time
    def current_day_index(self):
        hours_elapsed = (timezone.now() - self.start_at).total_seconds() / 3600
        return int(hours_elapsed // 24) + 1


class NutritionPlanWeek(models.Model):
    plan = models.ForeignKey(
        NutritionPlan, on_delete=models.CASCADE, db_column='plan_id',
        related_name='weeks'
    )
    number_week = models.IntegerField()

    class Meta:
        db_table = 'Nutrition_plans_weeks'


class NutritionPlanDay(models.Model):
    number_day = models.PositiveSmallIntegerField()
    week = models.ForeignKey(
        NutritionPlanWeek, on_delete=models.CASCADE, db_column='week_id',
        related_name='days'
    )
    name_day = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'Nutrition_plans_days'
        constraints = [
            models.UniqueConstraint(
                fields=['number_day', 'week'], name='uq_nutritionday_number_week'
            )
        ]


class NutritionPlanMeal(models.Model):
    day = models.ForeignKey(
        NutritionPlanDay, on_delete=models.CASCADE, db_column='day_id',
        related_name='meals'
    )
    meal_number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=100, default='Meal')

    class Meta:
        db_table = 'Nutrition_plans_meals'
        constraints = [
            models.UniqueConstraint(
                fields=['meal_number', 'day'], name='uq_nutritionmeal_number_day'
            )
        ]


class MealFood(models.Model):
    plan_meal = models.ForeignKey(
        NutritionPlanMeal, on_delete=models.CASCADE, db_column='plan_meal_id',
        related_name='foods'
    )
    # نص لأنو Edamam بترجع foodId كنص (مثلاً "food_a1gb9ubb72c...") مش رقم متل USDA fdcId
    api_id_food = models.CharField(max_length=100)
    name = models.CharField(max_length=200, null=True, blank=True)
    quantity = models.CharField(max_length=50)
    calories = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    protein = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    carbs = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    fat = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    fiber = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    class Meta:
        db_table = 'Meals_foods'
