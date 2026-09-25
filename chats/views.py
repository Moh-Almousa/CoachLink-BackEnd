from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser

from users.models import User
from subscriptions.models import SubscriptionPlayer
from .models import ChatMessage,ChatConversation
from .serializers import ChatMessageSerializer,ConversationListSerializer,SendMessageInputSerializer

from drf_spectacular.utils import extend_schema,OpenApiResponse ,inline_serializer
from rest_framework import serializers

# Check for an active subscription between the coach and player
def has_active_subscription(coach,player):
    return SubscriptionPlayer.objects.filter(player=player,
                                             package__coach=coach,
                                             status=SubscriptionPlayer.Status.ACTIVE).exists()

# Check that the user is a participant in the conversation
def is_conversation_participant(user,conversation):
    if user.role==User.Role.PLAYER:
        return conversation.player == user.player_profile
    if user.role==User.Role.COACH:
        return conversation.coach == user.coach_profile
    return False

# Resolve the (coach, player) pair from the receiver id
def resolve_other_party(request_user,other_user_id):
    # بيرجع (coach_profile, player_profile) اعتماداً على دور المستخدم الحالي
    other_user=User.objects.get(id=other_user_id)
    if request_user.role == User.Role.PLAYER:
        return other_user.coach_profile,request_user.player_profile
    return request_user.coach_profile,other_user.player_profile

# ============================================================================
# GET /api/chat/conversations/  - جلب كل محادثات المستخدم الحالي (لاعب أو كوتش)
# ============================================================================
class ConversationListView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="Get All Chat",
        description="ارجاع كل الدردشات",
        responses={200:ConversationListSerializer(many=True)}
    )

    def get(self,request):
        user = request.user
        if user.role==User.Role.PLAYER:
            conversation=ChatConversation.objects.filter(player=user.player_profile).select_related('coach__user','player__user')
        else:
            conversation=ChatConversation.objects.filter(coach=user.coach_profile).select_related('coach__user','player__user')
             # side effect: أي رسالة وصلتلي وحالتها sent بتصير delivered
        ChatMessage.objects.filter(chat__in=conversation, status=ChatMessage.Status.SENT).exclude(sent_by=user).update(status=ChatMessage.Status.DELIVERED)

        data = []
        for conv in conversation:
            is_player = user.role == User.Role.PLAYER
            other_profile = conv.coach if is_player else conv.player
            other_user = other_profile.user
            last_msg = conv.messages.order_by('-sent_at').first()

            data.append({
                'id': conv.id,
                'other_user': {
                    'id': other_user.id,
                    'name': other_user.full_name,
                    'image': other_profile.image_profile_url.url if other_profile.image_profile_url else None,
                },
                'is_active': has_active_subscription(conv.coach, conv.player),
                'last_message': {
                    'preview': last_msg.content or 'Attachment',
                    'sent_at': last_msg.sent_at,
                    'has_attachment': bool(last_msg.attachment),
                } if last_msg else None,
                'updated_at': conv.updated_at,
            })

        data.sort(key=lambda c: c['last_message']['sent_at'] if c['last_message'] else timezone.datetime.min.replace(tzinfo=timezone.UTC), reverse=True)
        serializer=ConversationListSerializer(data,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

# ============================================================================
# GET /api/chat/conversations/<pk>/messages/  - رسائل محادثة وحدة كاملة
# ============================================================================
class ConversationMessagesView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="Get All Messagaes",
        description="ارجاع كل الرسائل لهذه الدردشة",
        responses={
            403:OpenApiResponse(description="You are not authorized to access"),
            200:ChatMessageSerializer(many=True),
        }
    )

    def get(self,request,pk):
        conversation=get_object_or_404(ChatConversation,id=pk)
        if not is_conversation_participant(request.user,conversation):
            return Response({"error": "You are not authorized to access"}, status=status.HTTP_403_FORBIDDEN)
        ChatMessage.objects.filter(
            chat=conversation, status__in=[ChatMessage.Status.SENT, ChatMessage.Status.DELIVERED]
        ).exclude(sent_by=request.user).update(status=ChatMessage.Status.READ)
        # اظهار الرسائل بترتيب
        messges=conversation.messages.order_by('sent_at')
        serializer=ChatMessageSerializer(messges,many=True,context={'request':request})
        return Response(serializer.data,status=status.HTTP_200_OK)

# ============================================================================
# POST /api/chat/messages/  - إرسال رسالة (الوحيدة المحمية بشرط الاشتراك النشط)
# ============================================================================
class SendMessageView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(
        summary="send Messages",
        description="ارسال رسالة ",
        request=SendMessageInputSerializer,
        responses={
            400:OpenApiResponse(description="Bad Request"),
            404:OpenApiResponse(description="Receiver not found"),
            403:OpenApiResponse(description="Subscription is not active"),
            201:ChatMessageSerializer(many=True)
        }
    )

    def post(self,request):
        serializer=SendMessageInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)
        try:
            coach, player =resolve_other_party(request.user,serializer.validated_data['receiver_id'])
        except User.DoesNotExist:
            return Response({"error":"Receiver not found"},status=status.HTTP_404_NOT_FOUND)
        if not has_active_subscription(coach,player):
            return Response({"error":"Subscription is not active"},status=status.HTTP_403_FORBIDDEN)
        conversation,_=ChatConversation.objects.get_or_create(coach=coach,player=player)
        message=ChatMessage.objects.create(chat=conversation,
                                           sent_by=request.user,
                                           content=serializer.validated_data.get('content',''),
                                           attachment=serializer.validated_data.get('attachment'),
                                           attachment_type=serializer.validated_data.get('attachment_type'),
                                           )
        conversation.updated_at=timezone.now()
        conversation.save(update_fields=['updated_at'])
        result=ChatMessageSerializer(message,context={'request':request})
        return Response(result.data,status=status.HTTP_201_CREATED)
        
