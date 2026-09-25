import calendar
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from django.shortcuts import get_object_or_404
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsVerifiedCoach
from users.models import PlayerProfile
from subscriptions.models import SubscriptionPlayer
from .models import ProgramPlanExercise, ProgramWeek, ProgramDay, ProgramDayExercise
from .serializers import CreateProgramSerializer, ProgramPlanSerializer,UpdateProgramSerializer, ProgramPlanEditSerializer

from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)


# فئات الجسم القياسية بمكتبة ExerciseDB - مستخدمة بس لتنويع نتائج التصفح
# الأولي (قبل ما المدرب يكتب أي بحث)
BROWSE_BODY_PARTS = [
    'back', 'cardio', 'chest', 'lower arms', 'lower legs',
    'neck', 'shoulders', 'upper arms', 'upper legs', 'waist',
]
EXERCISES_PER_BODY_PART = 2  # 10 فئات * 2 = 20 تمرين متنوع بالتصفح الأولي


class ExerciseSearchView(APIView):
    """بروكسي لمكتبة ExerciseDB (RapidAPI) — يخبي المفتاح السري ومايعرضه للفرونت إند."""
    permission_classes = [IsAuthenticated, IsVerifiedCoach]
    @extend_schema(
        summary="Get Exercise Laibary",
        description="ارجاع قائمة التمارين من المكتبة وفلترة البحث ، خاصة للكوتشات الموثوقين",
        responses={
            200:inline_serializer(
                name="ExerciseSerachRespons",
                fields={
                    'id': serializers.IntegerField(),
                    'name': serializers.CharField(),
                    'target': serializers.CharField(),
                    'body_part': serializers.CharField(),
                    'equipment': serializers.CharField(),
                },
                many=True,
            ),
            502:OpenApiResponse(description="Could not reach the exercise library right now."),

        }
    )

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        host = settings.EXERCISEDB_RAPIDAPI_HOST
        headers = {
            'X-RapidAPI-Key': settings.EXERCISEDB_RAPIDAPI_KEY,
            'X-RapidAPI-Host': host,
        }

        if search:
            try:
                response = requests.get(
                    f'https://{host}/exercises/name/{search}',
                    headers=headers,
                    params={'limit': 20},
                    timeout=8,
                )
                response.raise_for_status()
                raw_exercises = response.json()
            except requests.RequestException:
                return Response(
                    {'error': 'Could not reach the exercise library right now.'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
        else:
            # No search term: fetch a few exercises per body part in parallel
            raw_exercises = []
            with ThreadPoolExecutor(max_workers=len(BROWSE_BODY_PARTS)) as executor:
                future_to_part = {
                    executor.submit(
                        requests.get,
                        f'https://{host}/exercises/bodyPart/{quote(part)}',
                        headers=headers,
                        params={'limit': EXERCISES_PER_BODY_PART},
                        timeout=8,
                    ): part
                    for part in BROWSE_BODY_PARTS
                }
                for future in as_completed(future_to_part):
                    try:
                        part_response = future.result()
                        part_response.raise_for_status()
                        raw_exercises.extend(part_response.json()[:EXERCISES_PER_BODY_PART])
                    except requests.RequestException:
                        # فئة وحدة فشلت (تايم اوت مثلاً) - نتجاهلها ونكمل بالباقي
                        continue

            if not raw_exercises:
                return Response(
                    {'error': 'Could not reach the exercise library right now.'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        # ملاحظة: هالمزوّد المحدد من ExerciseDB ما بيرجع صورة/gif مع نتيجة البحث (تحققنا فعلياً)
        exercises = [
            {
                'id': int(exercise['id']),
                'name': exercise.get('name'),
                'target': exercise.get('target'),
                'body_part': exercise.get('bodyPart'),
                'equipment': exercise.get('equipment'),
            }
            for exercise in raw_exercises
        ]
        return Response(exercises, status=status.HTTP_200_OK)


class CoachCreateProgramView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedCoach]
    @extend_schema(
        summary="Create Program ",
        description="انشاء برنامج تمارين من قبل الكوتش  ، خاصة للكوتشات الموثوقين",
        request=CreateProgramSerializer,
        responses={
            400:OpenApiResponse(description="This player does not have an active subscription with you."),
            201:ProgramPlanSerializer,
        }
    )

    def post(self, request):
        serializer = CreateProgramSerializer(data=request.data)
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

        with transaction.atomic():
            # كل إنشاء بينعمل برنامج جديد ومنفصل، وبرامج اللاعب السابقة بتضل مسجلة كسجل تاريخي
            start_at = timezone.now()
            plan = ProgramPlanExercise.objects.create(
                coach=coach,
                player=player,
                name=data['name'],
                start_at=start_at,
                end_at=add_months(start_at, data['number_of_months']),
            )

            for week_data in data['weeks']:
                week = ProgramWeek.objects.create(plan=plan, number_week=week_data['number_week'])
                for day_data in week_data['days']:
                    day = ProgramDay.objects.create(
                        week=week,
                        number_day=day_data['number_day'],
                        name_day=f"Day {day_data['number_day']}",
                    )
                    for exercise_data in day_data['exercises']:
                        ProgramDayExercise.objects.create(program_day=day, **exercise_data)

        output_serializer = ProgramPlanSerializer(plan, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class CoachEditeProgame(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedCoach]

    def _has_active_subscription(self, coach, player):
        return SubscriptionPlayer.objects.filter(
            player=player, package__coach=coach, status=SubscriptionPlayer.Status.ACTIVE
        ).exists()

    def _get_active_plan(self, coach, player):
        # Unfinished plans, newest first
        return ProgramPlanExercise.objects.filter(
            player=player, coach=coach, end_at__gt=timezone.now()
        ).order_by('-created_at')

    def _sync_day_exercises(self, day, exercises_data, number_week, number_day):
        """Update/create exercises the coach sent, delete ones they dropped. Returns an error message, or None on success."""
        existing_exercises = {exercise.id: exercise for exercise in day.exercises.all()}
        submitted_ids = {exercise_data['id'] for exercise_data in exercises_data if exercise_data.get('id')}

        for exercise_id, exercise in existing_exercises.items():
            if exercise_id not in submitted_ids:
                exercise.delete()

        for exercise_data in exercises_data:
            exercise_id = exercise_data.get('id')
            if exercise_id:
                exercise = existing_exercises.get(exercise_id)
                if not exercise:
                    return f"Exercise {exercise_id} does not belong in week {number_week} day {number_day}"
                exercise.api_id_exercise = exercise_data['api_id_exercise']
                exercise.name = exercise_data['name']
                exercise.video_url = exercise_data.get('video_url')
                exercise.weight = exercise_data['weight']
                exercise.sets = exercise_data['sets']
                exercise.reps = exercise_data['reps']
                exercise.save()
            else:
                ProgramDayExercise.objects.create(
                    program_day=day,
                    api_id_exercise=exercise_data['api_id_exercise'],
                    name=exercise_data['name'],
                    video_url=exercise_data['video_url'],
                    weight=exercise_data['weight'],
                    sets=exercise_data['sets'],
                    reps=exercise_data['reps'],
                )
        return None

    @extend_schema(
        summary="Get Active program for Player",
        description=" ارجاع برنامج اللاعب الذي تم اختياره في حال كان لدية برنامج نشط ، خاصة للكوتشات الموثوقين شرط ان يكون الكوتش واللاعب مرتبطين باشتراك نشط",
        responses={
            400:OpenApiResponse(description="This player does not have an active subscription with you."),
            200:inline_serializer(
                name="ActiveProgramResponse",
                fields={
                    'has_plan':serializers.BooleanField(),
                    'plan':ProgramPlanEditSerializer(allow_null=True)
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

        active_plan = self._get_active_plan(coach, player).prefetch_related('weeks__days__exercises').first()
        if not active_plan:
            return Response({'has_plan': False, 'plan': None}, status=status.HTTP_200_OK)

        serializer = ProgramPlanEditSerializer(active_plan, context={'request': request})
        return Response({'has_plan': True, 'plan': serializer.data}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Edite Program",
        description="تعديل برنامج لاعب من قبل الكوتش ، خاصة للكوتش الموثوق و شرط ان يكون الكوتش واللاعب مرتبطين باشتراك نشط",
        request=UpdateProgramSerializer,
        responses={
            400:OpenApiResponse(description="This player does not have an active subscription with you or week {number_week} does not exist or day {number_day} does not exist"),
            404:OpenApiResponse(description="Player does not have an active program."),
            200:ProgramPlanSerializer
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
            return Response({'error': 'Player does not have an active program.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateProgramSerializer(data=request.data, context={'request': request}, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            if 'name' in data:
                active_plan.name = data['name']

            for week_data in data.get('weeks', []):
                number_week = week_data['number_week']
                week = active_plan.weeks.filter(number_week=number_week).first()
                if not week:
                    return Response({'error': f'week {number_week} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                for day_data in week_data['days']:
                    number_day = day_data['number_day']
                    day = week.days.filter(number_day=number_day).first()
                    if not day:
                        return Response({'error': f'day {number_day} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                    error = self._sync_day_exercises(day, day_data['exercises'], number_week, number_day)
                    if error:
                        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            active_plan.save()

        output_serializer = ProgramPlanSerializer(active_plan, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)