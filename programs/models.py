from django.utils import timezone

from django.core.validators import MinValueValidator
from django.db import models

from users.models import CoachProfile, PlayerProfile

# Create your models here.
class ProgramPlanExercise(models.Model):
    coach = models.ForeignKey(
        CoachProfile, on_delete=models.PROTECT, db_column='coach_id',
        related_name='program_plans'
    )
    player = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, db_column='player_id',
        related_name='program_plans'
    )
    name = models.CharField(max_length=100)
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField()
    created_at = models.DateTimeField(
        default=timezone.now, null=True, blank=True, db_column='creat_at'
    )
    updated_at = models.DateField(auto_now=True)

    class Meta:
        db_table = 'Program_Plans_Exercises'


class ProgramWeek(models.Model):
    plan = models.ForeignKey(
        ProgramPlanExercise, on_delete=models.CASCADE, db_column='plan_id',
        related_name='weeks'
    )
    number_week = models.IntegerField()

    class Meta:
        db_table = 'Program_Week'


class ProgramDay(models.Model):
    number_day = models.PositiveSmallIntegerField()
    week = models.ForeignKey(
        ProgramWeek, on_delete=models.CASCADE, db_column='week_id',
        related_name='days'
    )
    name_day = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'Program_days'
        constraints = [
            models.UniqueConstraint(
                fields=['number_day', 'week'], name='uq_programday_number_week'
            )
        ]


class ProgramDayExercise(models.Model):
    program_day = models.ForeignKey(
        ProgramDay, on_delete=models.CASCADE, db_column='progame_day',
        related_name='exercises'
    )
    api_id_exercise = models.IntegerField()
    name = models.CharField(max_length=100, null=True, blank=True)
    video_url = models.CharField(max_length=255, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, db_column='weigth',
                                  validators=[MinValueValidator(0)])
    sets = models.PositiveSmallIntegerField()
    reps = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'Program_days_exercises'