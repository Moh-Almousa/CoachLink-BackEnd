from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from django.db import transaction
from users.permissions import IsPlayer
from users.models import User,PlayerProfile
from subscriptions.models import SubscriptionPlayer
from programs.models import ProgramDayExercise,ProgramPlanExercise
from programs.serializers import ProgramPlanSerializer
from ..models import WorkoutLog,WorkoutSetLog
from ..serializers import WorkoutLogSerializer,WorkoutSetLogSerializer

from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

def compute_workout_day_statuses(plan):
    now = timezone.now()
    hours_elapsed = (now - plan.start_at).total_seconds() / 3600
    current_day_index = int(hours_elapsed // 24) + 1

    statuses = []
    for week in plan.weeks.order_by('number_week'):
        days = list(week.days.order_by('number_day'))
        rest_credit = sum(1 for d in days if d.exercises.count() == 0)
        missed_so_far = 0

        for day in days:
            day_index = (week.number_week - 1) * 7 + day.number_day
            exercises = list(day.exercises.all())

            if not exercises:  # يوم راحة
                statuses.append({'week': week.number_week, 'day': day.number_day, 'status': 'rest'})
                continue
            if day_index > current_day_index:
                statuses.append({'week': week.number_week, 'day': day.number_day, 'status': 'planned'})
                continue

            all_logged = all(ex.workout_logs.exists() for ex in exercises)

            if day_index == current_day_index:
                s = 'complete' if all_logged else 'continue'
            elif all_logged:
                s = 'complete'
            else:
                missed_so_far += 1
                s = 'grace_used' if missed_so_far <= rest_credit else 'truant'

            statuses.append({'week': week.number_week, 'day': day.number_day, 'status': s})
    return statuses

    

class LogWorkoutView(APIView):
    permission_classes=[IsAuthenticated,IsPlayer]
    @extend_schema(
        summary="Create Log WorkOut",
        description="انشاء سجل تنفيذ تمرين",
        request=inline_serializer(
            name="WorkoutLogRequest",
            fields={
                "exercise": serializers.ListField(
                    child=inline_serializer(
                        name="ExerciseLogRequest",
                        fields={
                            "program_day_exercise_id": serializers.IntegerField(),
                            "note": serializers.CharField(
                                required=False,
                                allow_blank=True
                            ),
                            "sets": serializers.ListField(
                                required=False,
                                child=inline_serializer(
                                    name="ExerciseSetRequest",
                                    fields={
                                        "set_number": serializers.IntegerField(),
                                        "reps": serializers.IntegerField(),
                                        "weight": serializers.DecimalField(
                                            max_digits=10,
                                            decimal_places=2
                                        ),
                                    }
                                )
                            ),
                        }
                    )
                )
            }
        ),

        responses={
            200:WorkoutLogSerializer,
            400:OpenApiResponse(description="exercise is required"),
            404:OpenApiResponse(description="exercise is not found"),
            403:OpenApiResponse(description="This exercise is not for you")
        }
    )

    def post(self,request):
        exercise_data=request.data.get('exercise')
        if not exercise_data:
            return Response({"error":"exercise is required"},status=status.HTTP_400_BAD_REQUEST)
        created_log=[]
        
        with transaction.atomic():
            for exercise_entry in exercise_data:
                try:
                    exercise=(ProgramDayExercise.objects.select_related('program_day__week__plan')
                      .get(id=exercise_entry.get('program_day_exercise_id')))
                except ProgramDayExercise.DoesNotExist:
                    return Response({"error":"exercise is not found"},status=status.HTTP_404_NOT_FOUND)
                if exercise.program_day.week.plan.player != request.user.player_profile:
                    return Response({"error":"This exercise is not for you."},status=status.HTTP_403_FORBIDDEN)
                log, _ =WorkoutLog.objects.update_or_create(program_day_exercise=exercise,
                                                            defaults={
                                                                'status':WorkoutLog.Status.COMPLETE,
                                                                'note':exercise_entry.get('note',''),
                                                            })
                for set_data in exercise_entry.get('sets',[]):
                    WorkoutSetLog.objects.update_or_create(workout_log=log,
                                                           set_number=set_data['set_number'],
                                                          defaults={'reps':set_data['reps'],
                                                           'weight':set_data['weight']})
                created_log.append(log)
        serializer=WorkoutLogSerializer(created_log,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

class WorkoutProfileView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="Get WorkOut Tap Profaile",
        description="ارجاع سجلات تنفيذ تمارين اللاعب ع بروفايل ",
        responses={
            400:OpenApiResponse(description="Player not found"),
            403:OpenApiResponse(description="You are not authorized to access"),
            200:inline_serializer(
                name="LogWorkOutResponse",
                fields={
                    "program":ProgramPlanSerializer(many=True),
                    "logs":WorkoutLogSerializer(many=True),
                    "day_status":serializers.ListField(allow_null=True)
                }
            )
        }
    )

    def get(self,request,pk):
        try:
            player=PlayerProfile.objects.get(id=pk)
        except PlayerProfile.DoesNotExist:
            return Response({"error":"Player not found"},status=status.HTTP_400_BAD_REQUEST)
        is_self=(
            request.user.role == User.Role.PLAYER
            and request.user.player_profile.id == player.id
        )
        is_subscribed_coach=(
            request.user.role == User.Role.COACH
            and SubscriptionPlayer.objects.filter(player=player,package__coach=request.user.coach_profile,
                                                  status=SubscriptionPlayer.Status.ACTIVE).exists()
                            )
        if not (is_self or is_subscribed_coach):
            return Response({"error":"You are not authorized to access"},status=status.HTTP_403_FORBIDDEN)
        plan=ProgramPlanExercise.objects.filter(player=player).order_by('-created_at').first()
        if not plan:
            return Response({"program":None , 'logs':[], 'day_status':[]},status=status.HTTP_200_OK)
        logs=WorkoutLog.objects.filter(program_day_exercise__program_day__week__plan=plan)
        program_serializer=ProgramPlanSerializer(plan ,context={'request':request})
        log_serializer=WorkoutLogSerializer(logs,many=True)
        day_status =compute_workout_day_statuses(plan)
        return Response({'program':program_serializer.data,'logs':log_serializer.data,'day_status':day_status},status=status.HTTP_200_OK)
    
