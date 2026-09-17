import calendar
from decimal import Decimal
from django.shortcuts import get_object_or_404
import requests
from django.db.models import Sum
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.models import PlayerProfile
from users.permissions import IsVerifiedCoach
from subscriptions.models import SubscriptionPlayer
from .models import NutritionPlan, NutritionPlanWeek, NutritionPlanDay, NutritionPlanMeal, MealFood
from .serializers import CreateNutritionPlanSerializer, NutritionPlanSerializer ,UpdatePlanSerializer, NutritionPlanEditSerializer
from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)


EDAMAM_PARSER_URL = 'https://api.edamam.com/api/food-database/v2/parser'

BROWSE_DEFAULT_TERMS = ['chicken', 'rice', 'egg', 'apple']
BROWSE_ITEMS_PER_TERM = 4

WANTED_NUTRIENTS = {
    'ENERC_KCAL': 'calories',
    'PROCNT': 'protein',
    'CHOCDF': 'carbs',
    'FAT': 'fat',
    'FIBTG': 'fiber',
}


def _extract_per_100g(food):
    nutrients = food.get('nutrients', {})
    return {key: nutrients.get(code) for code, key in WANTED_NUTRIENTS.items()}


def _edamam_search(query):
    response = requests.get(
        EDAMAM_PARSER_URL,
        params={
            'ingr': query,
            'app_id': settings.EDAMAM_APP_ID,
            'app_key': settings.EDAMAM_APP_KEY,
        },
        timeout=8,
    )
    response.raise_for_status()
    hints = response.json().get('hints', [])
    return [hint['food'] for hint in hints if hint.get('food', {}).get('category') == 'Generic foods']


class FoodSearchView(APIView):

    permission_classes = [IsAuthenticated, IsVerifiedCoach] 

    @extend_schema(
        summary="Get Food Libary",
        description="ارجاع الطعام من المكتبة الغذائية وعملية البحث عن طعام",
        responses={
            502:OpenApiResponse(description="Could not reach the food library right now."),
            200:inline_serializer(
                name="FoodSerachResponse",
                fields={
                'id': serializers.IntegerField(),
                'name': serializers.CharField(),
                'per_100g': serializers.IntegerField(),
                }
            ),
        }
    )

    def get(self, request):
        search = request.query_params.get('search', '').strip()

        try:
            if search:
                raw_foods = _edamam_search(search)[:20]
            else:
                raw_foods = []
                for term in BROWSE_DEFAULT_TERMS:
                    raw_foods.extend(_edamam_search(term)[:BROWSE_ITEMS_PER_TERM])
        except requests.RequestException:
            return Response(
                {'error': 'Could not reach the food library right now.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        foods = [
            {
                'id': food.get('foodId'),
                'name': food.get('label'),
                'per_100g': _extract_per_100g(food),
            }
            for food in raw_foods
        ]
        return Response(foods, status=status.HTTP_200_OK)


class CoachCreateNutritionPlanView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedCoach]

    @extend_schema(
        summary="Create Nutrition plan",
        description="انشاء خطة غذائبة للاعب ، خاصة للكوتشات الموثوقين بشرط وجود ارتباط بين كوتش و الاعب باشتراك فعال",
        request=CreateNutritionPlanSerializer,
        responses={
            400:OpenApiResponse(description="This player does not have an active subscription with you."),
            200:NutritionPlanSerializer(many=True),
        }
    )

    def post(self, request):
        serializer = CreateNutritionPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        coach = request.user.coach_profile
        player = data['player']

        if not SubscriptionPlayer.objects.filter(
            player=player, package__coach=coach, status=SubscriptionPlayer.Status.ACTIVE
        ).exists():
            return Response(
                {'error': 'This player does not have an active subscription with you.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # مجموع القيم الغذائية الكاملة للخطة = مجموع كل صنف طعام بكل الأسابيع/الأيام/الوجبات
        total_calories = total_protein = total_carbs = total_fat = total_fiber = Decimal('0')
        for week_data in data['weeks']:
            for day_data in week_data['days']:
                for meal_data in day_data['meals']:
                    for food_data in meal_data['foods']:
                        total_calories += food_data['calories']
                        total_protein += food_data['protein']
                        total_carbs += food_data['carbs']
                        total_fat += food_data['fat']
                        total_fiber += food_data['fiber']

        with transaction.atomic():
            # خطة نشطة وحدة بس لكل لاعب بأي لحظة، والخطط القديمة تضل مسجلة كسجل تاريخي
            NutritionPlan.objects.filter(player=player, is_active=True).update(is_active=False)

            start_at = timezone.now()
            plan = NutritionPlan.objects.create(
                coach=coach,
                player=player,
                name=data['name'],
                note=data.get('note'),
                start_at=start_at,
                end_at=add_months(start_at, data['number_of_months']),
                calories_target=total_calories,
                protein_target=total_protein,
                carbs_target=total_carbs,
                fat_target=total_fat,
                fiber_target=total_fiber,
                is_active=True,
            )

            for week_data in data['weeks']:
                week = NutritionPlanWeek.objects.create(plan=plan, number_week=week_data['number_week'])
                for day_data in week_data['days']:
                    day = NutritionPlanDay.objects.create(
                        week=week,
                        number_day=day_data['number_day'],
                        name_day=f"Day {day_data['number_day']}",
                    )
                    for meal_data in day_data['meals']:
                        meal = NutritionPlanMeal.objects.create(
                            day=day,
                            meal_number=meal_data['meal_number'],
                            name=meal_data.get('name') or f"Meal {meal_data['meal_number']}",
                        )
                        for food_data in meal_data['foods']:
                            MealFood.objects.create(plan_meal=meal, **food_data)

        output_serializer = NutritionPlanSerializer(plan, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class _PlanEditError(Exception):
    """Raised inside the atomic PATCH block so an invalid edit rolls back instead of partially committing."""

    def __init__(self, message):
        self.message = message


class CoachEidteNutritionPlanView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedCoach]

    def _has_active_subscription(self, coach, player):
        return SubscriptionPlayer.objects.filter(
            player=player, package__coach=coach, status=SubscriptionPlayer.Status.ACTIVE
        ).exists()

    def _get_active_plan(self, coach, player):
        return NutritionPlan.objects.filter(coach=coach, player=player, is_active=True)

    def _sync_meal_foods(self, meal, foods_data):
        existing_foods = {food.id: food for food in meal.foods.all()}
        submitted_ids = {food_data['id'] for food_data in foods_data if food_data.get('id')}

        for food_id, food in existing_foods.items():
            if food_id not in submitted_ids:
                food.delete()

        for food_data in foods_data:
            food_id = food_data.get('id')
            if food_id:
                food = existing_foods.get(food_id)
                if not food:
                    raise _PlanEditError(f"food {food_id} does not belong to this meal")
            else:
                food = MealFood(plan_meal=meal)

            food.api_id_food = food_data['api_id_food']
            food.name = food_data.get('name')
            food.quantity = food_data['quantity']
            food.calories = food_data['calories']
            food.protein = food_data['protein']
            food.carbs = food_data['carbs']
            food.fat = food_data['fat']
            food.fiber = food_data['fiber']
            food.save()

    def _sync_day_meals(self, day, meals_data):
        existing_meals = {meal.id: meal for meal in day.meals.all()}
        submitted_ids = {meal_data['id'] for meal_data in meals_data if meal_data.get('id')}

        for meal_id, meal in existing_meals.items():
            if meal_id not in submitted_ids:
                meal.delete()

        for meal_data in meals_data:
            meal_id = meal_data.get('id')
            if meal_id:
                meal = existing_meals.get(meal_id)
                if not meal:
                    raise _PlanEditError(f"meal {meal_id} does not belong to this day")
            else:
                meal = NutritionPlanMeal(day=day)

            meal.meal_number = meal_data['meal_number']
            meal.name = meal_data.get('name') or f"Meal {meal_data['meal_number']}"
            meal.save()

            self._sync_meal_foods(meal, meal_data.get('foods', []))

    def _recompute_targets(self, plan):
        totals = MealFood.objects.filter(plan_meal__day__week__plan=plan).aggregate(
            calories=Sum('calories'), protein=Sum('protein'),
            carbs=Sum('carbs'), fat=Sum('fat'), fiber=Sum('fiber'),
        )
        plan.calories_target = totals['calories'] or Decimal('0')
        plan.protein_target = totals['protein'] or Decimal('0')
        plan.carbs_target = totals['carbs'] or Decimal('0')
        plan.fat_target = totals['fat'] or Decimal('0')
        plan.fiber_target = totals['fiber'] or Decimal('0')

    @extend_schema(
        summary="Get Active Plan This Player",
        description="ارجاع خطة اللاعب في حال كانت لديه خطة نشطة ، خاصة للكوتشات الموثوقين ولديهم اشتراك مع اللاعب نشط",
        responses={
            400:OpenApiResponse(description="This player does not have an active subscription with you."),
            200:inline_serializer(
                name="ActivePlanResponse",
                fields={
                    'has_plan':serializers.BooleanField(),
                    'plan':NutritionPlanEditSerializer(allow_null=True)
                }
            )
        }
    )

    def get(self, request, pk):
        coach = request.user.coach_profile
        player = get_object_or_404(PlayerProfile, id=pk)

        if not self._has_active_subscription(coach, player):
            return Response(
                {'error': 'This player does not have an active subscription with you.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_plan = self._get_active_plan(coach, player).prefetch_related('weeks__days__meals__foods').first()
        if not active_plan:
            return Response({'has_plan': False, 'plan': None}, status=status.HTTP_200_OK)

        serializer = NutritionPlanEditSerializer(active_plan, context={'request': request})
        return Response({'has_plan': True, 'plan': serializer.data}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Edite Nutrition Plan",
        description="تعديل خطة لاعب من قبل الكوتش ، خاصة للكوتش الموثوق و شرط ان يكون الكوتش واللاعب مرتبطين باشتراك نشط",
        request=UpdatePlanSerializer,
        responses={
            400:OpenApiResponse(description="This player does not have an active subscription with you "),
            404:OpenApiResponse(description="Player does not have an active plan."),
            200:NutritionPlanSerializer(many=True)
        }
    )

    def patch(self, request, pk):
        coach = request.user.coach_profile
        player = get_object_or_404(PlayerProfile, id=pk)

        if not self._has_active_subscription(coach, player):
            return Response(
                {'error': 'This player does not have an active subscription with you.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_plan = self._get_active_plan(coach, player).first()
        if not active_plan:
            return Response({'error': 'Player does not have an active plan.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdatePlanSerializer(data=request.data, context={'request': request}, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            with transaction.atomic():
                if 'name' in data:
                    active_plan.name = data['name']
                if 'note' in data:
                    active_plan.note = data['note']

                for week_data in data.get('weeks', []):
                    number_week = week_data['number_week']
                    week = active_plan.weeks.filter(number_week=number_week).first()
                    if not week:
                        raise _PlanEditError(f'week {number_week} does not exist')

                    for day_data in week_data['days']:
                        number_day = day_data['number_day']
                        day = week.days.filter(number_day=number_day).first()
                        if not day:
                            raise _PlanEditError(f'day {number_day} does not exist')

                        self._sync_day_meals(day, day_data['meals'])

                self._recompute_targets(active_plan)
                active_plan.save()
        except _PlanEditError as exc:
            return Response({'error': exc.message}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = NutritionPlanSerializer(active_plan, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)
