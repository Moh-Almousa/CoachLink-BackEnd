from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsPlayer
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
from users.models import PlayerProfile ,User
from subscriptions.models import SubscriptionPlayer
from nutritions.models import (NutritionPlanMeal,MealFood,NutritionPlan)
from nutritions.serializers import NutritionPlanSerializer
from ..models import NutritionLog
from ..serializers.nutritionlog_serializers import( NutritionLogSerializer,
                                                   )
from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

# تسجيل "غياب" حقيقي (log فعلي بقيم 0) لأي وجبة تبع يوم فات ومالها لوج
# إطلاقاً - بتشتغل كـ backfill لما اللاعب (أو الكوتش) يفتح NutritionProfileView،
# مش بشكل مجدول تلقائياً (ما في scheduler بالمشروع - قرار 2026-08-16).
# idempotent: get_or_create بمفتاح meal، فما بتكرر لو انعملت قبل لنفس الوجبة.
def backfill_missed_nutrition_logs(plan):
    current_day_index = plan.current_day_index()

    for week in plan.weeks.all():
        for day in week.days.all():
            day_index = (week.number_week - 1) * 7 + day.number_day
            if day_index >= current_day_index:
                continue  # اليوم الحالي أو لسا ما وصل - مش "فايت" بعد
            for meal in day.meals.all():
                NutritionLog.objects.get_or_create(
                    meal=meal,
                    defaults={
                        'status': NutritionLog.Status.TRUANT,
                        'calories_total': Decimal('0'),
                        'protein': Decimal('0'),
                        'carbs': Decimal('0'),
                        'fat': Decimal('0'),
                        'fiber': Decimal('0'),
                    },
                )


class LogMealCompletionView(APIView):
    permission_classes=[IsAuthenticated,IsPlayer]
    @extend_schema(
        summary="create log nutirtion meal in day",
        description="انشاء سجل تتبع للوجبات",
        request=NutritionLogSerializer,
        responses={
            200:NutritionLogSerializer,
            403:OpenApiResponse(response=inline_serializer(
                name="ErrorRespons",
                fields={
                    "error":serializers.CharField(),
                }
                ),description=(
                "Possible reasons:\n"
                "- User does not have permission.\n"
                "- Coach is not verified.\n"
                "- User is not allowed to access this resource."
                )
                )
                }
    )

    def post(self,request):
        meal_id=request.data.get('meal_id')
        if not meal_id :
            return Response({"error": "meal_id not found"},status=status.HTTP_400_BAD_REQUEST)
        try:
            meal=NutritionPlanMeal.objects.select_related('day__week__plan').get(id=meal_id)
        except NutritionPlanMeal.DoesNotExist:
            return Response({"error": "NutritionPlanMeal not found"},status=status.HTTP_404_NOT_FOUND)
        if not meal.day.week.plan.player == request.user.player_profile :
            return Response({"message": "This meal is not for you"},status=status.HTTP_403_FORBIDDEN)
        if not meal.day.week.plan.is_active == True :
            return Response({"message": "The plan is not active."},status=status.HTTP_403_FORBIDDEN)

        # اليوم لازم يكون "اليوم الحالي" بالضبط (مش فايت، مش لسا ما وصل) -
        # وإلا اليوم يا إما مقفول (فاتو وقتو، لازم يصير truant عبر backfill
        # لما البروفايل ينقرا) أو لسا ما إجا دوره. بدون هالتحقق كان ممكن
        # اللاعب يشيّك وجبة قديمة صارت truant أصلاً ويبدّلها complete متأخر.
        day = meal.day
        meal_day_index = (day.week.number_week - 1) * 7 + day.number_day
        if meal_day_index != meal.day.week.plan.current_day_index():
            return Response({"error": "You can only log today's meals."}, status=status.HTTP_403_FORBIDDEN)

        totals=(MealFood.objects.filter(plan_meal=meal).aggregate(
                    calories_total=Coalesce(Sum('calories'),Decimal('0')),
                    protein=Coalesce(Sum('protein'),Decimal('0')),
                    carbs=Coalesce(Sum('carbs'),Decimal('0')),
                    fat=Coalesce(Sum('fat'),Decimal('0')),
                    fiber=Coalesce(Sum('fiber'),Decimal('0')),
                    ))
        log,created=NutritionLog.objects.update_or_create(
            meal=meal,
            defaults={
                'status': NutritionLog.Status.COMPLETE,
                'calories_total': totals['calories_total'],
                'protein': totals['protein'],
                'carbs': totals['carbs'],
                'fat': totals['fat'],
                'fiber': totals['fiber'],
            }
        )
        serializer=NutritionLogSerializer(log)
        return Response(serializer.data,status=status.HTTP_200_OK)

class NutritionProfileView (APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="Get Tap Nutirtion profaile",
        description="ارجاع سجلات تنفيذ اللاعب للوجبات في بروفايل لاعب",
        responses={
            404:OpenApiResponse(description="Player not found"),
            403:OpenApiResponse(description="You do not have permission to access this player's data"),
            200:inline_serializer(
                name="TapNutirtionProfaile",
                fields={
                    "logs":NutritionLogSerializer(many=True),
                    "plan":NutritionPlanSerializer(many=True),
                }
            )
        }
    )

    def get(self,request,pk):
        try:
            player=PlayerProfile.objects.get(id=pk)
        except PlayerProfile.DoesNotExist:
            return Response({"error":"Player not found"},status=status.HTTP_404_NOT_FOUND)
        is_self = (
            request.user.role == User.Role.PLAYER
            and request.user.player_profile.id == player.id
            )

        is_subscribed_coach = (
            request.user.role == User.Role.COACH
            and SubscriptionPlayer.objects.filter(
                player=player,
                package__coach=request.user.coach_profile,
                status=SubscriptionPlayer.Status.ACTIVE
            ).exists()
        )

        if not (is_self or is_subscribed_coach):
            return Response(
                {"error": "You do not have permission to access this player's data."},
                status=status.HTTP_403_FORBIDDEN
            )
        # آخر خطة اتعملت لهاد اللاعب - بغض النظر عن is_active، لأنو هاد البروفايل
        # بيمثل آخر تنفيذ لآخر خطة، مش شرط تكون نشطة رسمياً هلق
        plan=NutritionPlan.objects.filter(player=player).order_by('-created_at').first()
        if not plan:
            return Response({"plan":None,"logs":[]},status=status.HTTP_200_OK)
        backfill_missed_nutrition_logs(plan)
        logs=NutritionLog.objects.filter(meal__day__week__plan=plan)
        logs_serializer=NutritionLogSerializer(logs,many=True)
        plan_serializer=NutritionPlanSerializer(plan,context={'request':request})
        return Response({"logs":logs_serializer.data , "plan":plan_serializer.data},status=status.HTTP_200_OK)