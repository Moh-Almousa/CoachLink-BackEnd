from decimal import Decimal

from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsPlayer , IsActivePlayerOfCoach
from ..serializers.player_serializers import (PlayerFitnessProfileSerializer, PlayerDashboardSerializer,
                                              RateCoachInputSerializer, CoachRatingSerializer,
                                              PlayerProfileOverviewSerializer)
from ..models import CoachRating
from users.models import PlayerProfile,User
from programs.models import ProgramPlanExercise
from subscriptions.models import SubscriptionPlayer
from nutritions.models import NutritionPlan, NutritionPlanDay
from logs.models import NutritionLog, DailyPhysicalHealth
from logs.serializers import DailyPhysicalHealthSerializer
from logs.views.workoutlog_views import compute_workout_day_statuses
from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

def calculate_age(birth_date):
    if not birth_date:
        return None
    today=timezone.now().date()
    return today.year - birth_date.year -((today.month,today.day)<(birth_date.month,birth_date.day))

class PlayerProfileOverviewView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="Get Player Profile Overview",
        description="ارجاع تاب بروفايل اللاعب و القسم العلوي الثابت",
        responses={
            200:PlayerProfileOverviewSerializer,
            404:OpenApiResponse(description="Player not found"),
            403:OpenApiResponse(description="You are not authorized to access"),
        }
    )
    def get(self, request, pk):
        try:
            player = PlayerProfile.objects.get(id=pk)
        except PlayerProfile.DoesNotExist:
            return Response({"error":"Player not found"}, status=status.HTTP_404_NOT_FOUND)

        is_self = (request.user.role == User.Role.PLAYER and request.user.player_profile.id == player.id)
        is_subscribed_coach = (request.user.role == User.Role.COACH and SubscriptionPlayer.objects.filter(
            player=player, package__coach=request.user.coach_profile,
            status=SubscriptionPlayer.Status.ACTIVE).exists())
        if not (is_self or is_subscribed_coach):
            return Response({"error":"You are not authorized to access"}, status=status.HTTP_403_FORBIDDEN)

        active_sub = (SubscriptionPlayer.objects.filter(player=player, status=SubscriptionPlayer.Status.ACTIVE)
                      .select_related('package__coach__user').order_by('-start_date').first())
        coach = active_sub.package.coach if active_sub else None

        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        latest_log = DailyPhysicalHealth.objects.filter(player=player).order_by('-date_day').first()
        latest_weight = latest_log.weight_kg if latest_log else player.weight_kg
        baseline_log = DailyPhysicalHealth.objects.filter(player=player, date_day__lt=start_of_month).order_by('-date_day').first()
        baseline_weight = baseline_log.weight_kg if baseline_log else player.weight_kg
        weight_change = (latest_weight - baseline_weight) if latest_weight is not None and baseline_weight is not None else None

        workout_plan = ProgramPlanExercise.objects.filter(player=player).order_by('-created_at').first()
        total_weeks_count = completed_weeks_count = 0
        if workout_plan:
            total_weeks_count = workout_plan.weeks.count()
            weeks_map = {}
            for entry in compute_workout_day_statuses(workout_plan):
                weeks_map.setdefault(entry['week'], []).append(entry['status'])
            completed_weeks_count = sum(1 for s in weeks_map.values() if all(x in ('rest','complete') for x in s))
        workout_progress_percent = round((completed_weeks_count/total_weeks_count)*100) if total_weeks_count else 0

        nutrition_plan = NutritionPlan.objects.filter(player=player).order_by('-created_at').first()
        carbs_percent = protein_percent = fat_percent = 0
        if nutrition_plan:
            protein_kcal = nutrition_plan.protein_target * 4
            carb_kcal = nutrition_plan.carbs_target * 4
            fat_kcal = nutrition_plan.fat_target * 9
            total_kcal = protein_kcal + carb_kcal + fat_kcal
            if total_kcal > 0:
                protein_percent = round(protein_kcal/total_kcal*100)
                carbs_percent = round(carb_kcal/total_kcal*100)
                fat_percent = round(fat_kcal/total_kcal*100)

        data = {
            'name': player.user.full_name,
            'image': player.image_profile_url.url if player.image_profile_url else None,
            'bio': player.bio,
            'coach_name': coach.user.full_name if coach else None,
            'plan_name': active_sub.package.name if active_sub else "No Plan",
            'age': calculate_age(player.user.birth_date),
            'height_cm': player.height_cm,
            'weight_kg': latest_weight,
            'weight_change_kg': weight_change,
            'training_age_years': player.training_age_years,
            'goal': player.goal,
            'health_status': player.note_sick,
            'has_injuries': player.is_injury,
            'injury_details': player.note_injury,
            'active_workout_name': workout_plan.name if workout_plan else None,
            'total_weeks_count': total_weeks_count,
            'completed_weeks_count': completed_weeks_count,
            'workout_progress_percent': workout_progress_percent,
            'active_nutrition_name': nutrition_plan.name if nutrition_plan else None,
            'active_nutrition_kcal': nutrition_plan.calories_target if nutrition_plan else None,
            'carbs_percent': carbs_percent,
            'protein_percent': protein_percent,
            'fat_percent': fat_percent,
        }
        return Response(PlayerProfileOverviewSerializer(data).data, status=status.HTTP_200_OK)

class PlayerFitnessProfileViews(APIView):
    permission_classes=[IsAuthenticated,IsPlayer]
    @extend_schema(
        summary="Update Player Fitness Profile",
        description="استبيان للاعب بعد اشتراكه عند كوتش يملأ معلومات مهنية عن نفسه وهدفه ووزنه وطوله وعمرك ومدة التدريب، خاصة للاعبين",
        request=PlayerFitnessProfileSerializer,
        responses={
            200:PlayerFitnessProfileSerializer,
            400:OpenApiResponse(description="Invalid input data"),
        }
    )
    def patch(self,request):
        player=request.user.player_profile
        serializer=PlayerFitnessProfileSerializer(player,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


# يوم التغذية الحالي محسوب بنفس مبدأ compute_workout_day_statuses بالتمارين
# (logs/views/workoutlog_views.py) - نفس صيغة current_day_index المعتمدة على
# الوقت الحقيقي المنقضي من start_at، مش على إكمال اللاعب فقط، حتى تبقى واقعية.
def get_current_nutrition_day_stats(plan):
    now = timezone.now()
    hours_elapsed = (now - plan.start_at).total_seconds() / 3600
    current_day_index = int(hours_elapsed // 24) + 1

    # نفس تحويل day_index لأسبوع/يوم بدورة 7 أيام المستخدم بالتمارين
    week_number = (current_day_index - 1) // 7 + 1
    day_number = (current_day_index - 1) % 7 + 1

    day = NutritionPlanDay.objects.filter(
        week__plan=plan, week__number_week=week_number, number_day=day_number
    ).first()

    if not day:
        return {'targetKcal': plan.calories_target, 'consumedKcal': Decimal('0')}

    consumed = NutritionLog.objects.filter(
        meal__day=day, status=NutritionLog.Status.COMPLETE
    ).aggregate(total=Coalesce(Sum('calories_total'), Decimal('0')))['total']

    return {'targetKcal': plan.calories_target, 'consumedKcal': consumed}


class PlayerDashboardView(APIView):
    permission_classes=[IsAuthenticated,IsPlayer]
    @extend_schema(
        summary="Get Player Dashboard Data",
        description="ارجاع بيانات لوجة تحكم اللاعب ، خاصة للاعبين",
        responses={200:PlayerDashboardSerializer}
    )    
    def get(self,request):
        player=request.user.player_profile

        active_sub=(SubscriptionPlayer.objects
                    .filter(player=player,status=SubscriptionPlayer.Status.ACTIVE)
                    .select_related('package__coach__user')
                    .order_by('-start_date').first())
        coach=active_sub.package.coach if active_sub else None
        days_left=max((active_sub.end_date - timezone.now()).days,0) if active_sub and active_sub.end_date else 0

        nutrition_plan=NutritionPlan.objects.filter(player=player).order_by('-created_at').first()
        nutr_stats=(get_current_nutrition_day_stats(nutrition_plan) if nutrition_plan
                    else {'targetKcal':Decimal('0'),'consumedKcal':Decimal('0')})

        weight_logs=DailyPhysicalHealth.objects.filter(player=player).order_by('-date_day')[:10]
        latest_weight=weight_logs[0].weight_kg if weight_logs else player.weight_kg

        data={
            'player_profile_id': player.id,
            'coach_name': coach.user.full_name if coach else None,
            'coach_image': coach.image_profile_url.url if coach and coach.image_profile_url else None,
            'coach_id': coach.id if coach else None,
            'coach_user_id': coach.user_id if coach else None,
            'package_name': active_sub.package.name if active_sub else "No Plan",
            'days_left': days_left,
            'target_kcal': nutr_stats['targetKcal'],
            'consumed_kcal': nutr_stats['consumedKcal'],
            'latest_weight_kg': latest_weight,
            'weight_logs': DailyPhysicalHealthSerializer(weight_logs,many=True).data,
        }
        serializer=PlayerDashboardSerializer(data)
        return Response(serializer.data,status=status.HTTP_200_OK)


# تقييم الكوتش - حصراً للاعب المشترك بباقة هاد الكوتش واشتراكو Active.
# IsActivePlayerOfCoach (users/permissions.py) بتعمل هاد الفحص لحالها قبل
# ما توصل post() أصلاً - بتقرا coachId من الـ body وبترجع 403 لو مش مشترك
# أو الاشتراك مش نشط، فما في داعي نكرر نفس التحقق هون.
class PlayerRateCoachView(APIView):
    permission_classes=[IsAuthenticated,IsPlayer,IsActivePlayerOfCoach]
    @extend_schema(
        summary="Rate Coach",
        description="تقييم اللاعبين الكوتش المشترك عنده ، خاصة للاعبين الذين لديه اشتراك نشط مع الكوتش",
        request=RateCoachInputSerializer,
        responses={200:CoachRatingSerializer}
    )
    def post(self,request):
        serializer=RateCoachInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

        rating_obj,_=CoachRating.objects.update_or_create(
            coach_id=serializer.validated_data['coachId'],
            player=request.user.player_profile,
            defaults={'rating':serializer.validated_data['rating']}
        )
        return Response(CoachRatingSerializer(rating_obj).data,status=status.HTTP_200_OK)

