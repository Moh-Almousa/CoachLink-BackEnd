from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from users.models import PlayerProfile ,User
from subscriptions.models import SubscriptionPlayer
from users.permissions import IsPlayer
from ..models import DailyPhysicalHealth,BodyMeasurement
from ..serializers import BodyMeasurementSerializer,DailyPhysicalHealthSerializer

from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

class LogWeightView(APIView):
    permission_classes=[IsAuthenticated,IsPlayer]

    @extend_schema(
        summary="Log Wight",
        description="تسجيل وزن اللاعب ، خاصة للاعبين",
        request=DailyPhysicalHealthSerializer,
        responses={
            201:DailyPhysicalHealthSerializer(many=True),
            400:OpenApiResponse(description="Bad Request")
        }
    )

    def post(self,request):
        serializer=DailyPhysicalHealthSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(player=request.user.player_profile)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    #Body:{"weight_kg": 74.50}
    
class WeightProfileView(APIView):
    permission_classes=[IsAuthenticated]

    @extend_schema(
        summary="Get Tap Weight Profaile",
        description="ارجاع تاب وزن في بروفايل اللاعب ، يمكن للاعب نفسه والكوتش  المشترك معه رؤيتها",
        responses={
            400:OpenApiResponse(description="Player not found"),
            403:OpenApiResponse(description="You are not authorized to access"),
            200:inline_serializer(
                name="TapWeightProfaileResponse",
                fields={
                    "weight_goal_kg":serializers.IntegerField(),
                    "logs":DailyPhysicalHealthSerializer(many=True)
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
        logs=DailyPhysicalHealth.objects.filter(player=player).order_by('-date_day')
        logs_serializer=DailyPhysicalHealthSerializer(logs,many=True)
        return Response({'weight_goal_kg':player.weight_goal_kg,'logs':logs_serializer.data},status=status.HTTP_200_OK)

class LogBodyMeasurementsView(APIView):
    permission_classes=[IsAuthenticated,IsPlayer]

    @extend_schema(
        summary="Create Log Body Measura",
        description="كتابات قياسات عضلات الجسم",
        request=BodyMeasurementSerializer,
        responses={
            400:OpenApiResponse(description="measurements is required"),
            201:BodyMeasurementSerializer(many=True)
        }
    )

    def post(self,request):
        measurement_data=request.data.get('measurements')
        if not measurement_data:
            return Response({"error": "measurements is required"},status=status.HTTP_400_BAD_REQUEST)
        created=[]
        with transaction.atomic():
            for m in measurement_data:
                obj,_=BodyMeasurement.objects.update_or_create(player=request.user.player_profile,
                                                               muscle_name=m['muscle_name'],
                                                               defaults={'value_cm':m['value_cm'],
                                                                         'date_day':timezone.now()})
                created.append(obj)
        serializer=BodyMeasurementSerializer(created,many=True)
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    
class BodyMeasurementsProfileView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="Get Boady Measura",
        description="ارجاع القياسات الجسدية في البروفايل ، يمكن للاعب نفسه والكوتش المشترك عندو رؤيتها",
        responses={
            200: inline_serializer(
                name="LatestBodyMeasurementsResponse",
                fields={
                    "chest": serializers.DecimalField(max_digits=10,decimal_places=2,allow_null=True),
                    "waist": serializers.DecimalField(max_digits=10,decimal_places=2,allow_null=True),
                    "hips": serializers.DecimalField(max_digits=10,decimal_places=2,allow_null=True),
                    "biceps": serializers.DecimalField(max_digits=10,decimal_places=2,allow_null=True),
                    "thighs": serializers.DecimalField(max_digits=10,decimal_places=2,allow_null=True),
                    "date": serializers.DateField(allow_null=True),
                },
            ),
            400:OpenApiResponse(description="Player not found"),
            403:OpenApiResponse(description="You are not authorized to access"),
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
        result={'date':None}
        for muscle_value,_ in BodyMeasurement.Muscle.choices:
            if muscle_value == BodyMeasurement.Muscle.OTHER:
                continue
            latest = BodyMeasurement.objects.filter(
                player=player, muscle_name=muscle_value
            ).order_by('-date_day').first()
            result[muscle_value] = latest.value_cm if latest else None
            if latest and (result['date'] is None or latest.date_day > result['date']):
                result['date'] = latest.date_day
        return Response(result)

