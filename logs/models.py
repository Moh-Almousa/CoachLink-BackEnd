from django.utils import timezone

from django.db import models
from django.core.validators import MinValueValidator

from nutritions.models import NutritionPlanMeal
from programs.models import ProgramDayExercise
from users.models import PlayerProfile

# Create your models here.
class WorkoutLog(models.Model):
    class Status(models.TextChoices):
        COMPLETE = 'complete', 'Complete'
        UNCOMPLETE = 'uncomplete', 'Uncomplete'
        REST = 'rest', 'Rest'
        TRUANT = 'truant', 'Truant'

    program_day_exercise = models.ForeignKey(
        ProgramDayExercise, on_delete=models.PROTECT, null=True, blank=True,
        db_column='program_day_exercise', related_name='workout_logs'
    )
    note = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=50, choices=Status.choices)
    date_day = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        db_table = 'Workout_logs'


class WorkoutSetLog(models.Model):
    workout_log = models.ForeignKey(
        WorkoutLog, on_delete=models.CASCADE, related_name='set_logs'
    )
    set_number = models.PositiveSmallIntegerField()
    reps = models.PositiveSmallIntegerField()
    # MinValueValidator(0) مش (1) - تمرين بوزن الجسم بس (بدون أوزان إضافية)
    # قيمته المنطقية صفر، مش لازم تكون موجبة تماماً متل وزن اللاعب نفسو
    weight = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        db_table = 'Workout_set_logs'
        constraints = [
            models.UniqueConstraint(
                fields=['workout_log', 'set_number'], name='uq_workoutsetlog_number'
            )
        ]

class NutritionLog(models.Model):
    class Status(models.TextChoices):
        COMPLETE = 'complete', 'Complete'
        TRUANT = 'truant', 'Truant'

    meal = models.ForeignKey(
        NutritionPlanMeal, on_delete=models.PROTECT, null=True, blank=True,
        db_column='meal_id', related_name='logs'
    )
    status = models.CharField(max_length=50, choices=Status.choices)
    date_day = models.DateTimeField(default=timezone.now, null=True, blank=True)
    calories_total = models.DecimalField(
        max_digits=18, decimal_places=0, null=True, blank=True
    )
    protein = models.DecimalField(
        max_digits=18, decimal_places=0, null=True, blank=True
    )
    carbs = models.DecimalField(
        max_digits=18, decimal_places=0, null=True, blank=True
    )
    fat = models.DecimalField(
        max_digits=18, decimal_places=0, null=True, blank=True
    )
    fiber = models.DecimalField(
        max_digits=18, decimal_places=0, null=True, blank=True
    )

    class Meta:
        db_table = 'Nutrition_logs'


class BodyMeasurement(models.Model):
    class Muscle(models.TextChoices):
        CHEST = 'chest', 'Chest'
        WAIST = 'waist', 'Waist'
        HIPS = 'hips', 'Hips'
        BICEPS = 'biceps', 'Biceps'
        THIGHS = 'thighs', 'Thighs'
        OTHER = 'other', 'Other'

    player = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, db_column='player_id',
        related_name='body_measurements'
    )
    muscle_name = models.CharField(max_length=50, choices=Muscle.choices)
    value_cm = models.DecimalField(
        max_digits=5, decimal_places=1,
        validators=[MinValueValidator(1)],
    )
    date_day = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        db_table = 'Body_measurement'


class DailyPhysicalHealth(models.Model):
    class EnergyLevel(models.TextChoices):
        LOW = 'low', 'Low'
        NORMAL = 'normal', 'Normal'
        HIGH = 'higth', 'High'  # القيمة في القاعدة مكتوبة higth

    class MuscleSoreness(models.TextChoices):
        NONE = 'none', 'None'
        SORE = 'sore', 'Sore'
        VERY_SORE = 'very sore', 'Very sore'

    player = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, db_column='player_id',
        related_name='daily_health'
    )
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, db_column='weigth_kg',
        validators=[MinValueValidator(1)],
    )
    energy_level = models.CharField(
        max_length=50, choices=EnergyLevel.choices, null=True, blank=True
    )
    muscle_soreness = models.CharField(
        max_length=50, choices=MuscleSoreness.choices, null=True, blank=True
    )
    note = models.CharField(max_length=500, null=True, blank=True)
    date_day = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        db_table = 'Daily_physical_health'
