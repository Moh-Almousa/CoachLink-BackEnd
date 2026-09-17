from rest_framework import serializers
from .models import  ChatConversation,ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model=ChatMessage
        fields=['id','chat','sent_by','content','attachment','attachment_type',
                'status','sent_at']
        read_only_fields=['id','chat','sent_by','status','sent_at']
        
class SendMessageInputSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    content = serializers.CharField(required=False, allow_blank=True)
    attachment = serializers.FileField(required=False)
    attachment_type = serializers.ChoiceField(choices=ChatMessage.AttachmentType.choices, required=False)
    def validate(self, attr):
        if not attr.get('content') and not attr.get('attachment'):
            raise serializers.ValidationError("content or attachment is required")
        return attr
    
class ConversationListSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    other_user = serializers.DictField()
    is_active = serializers.BooleanField()
    last_message = serializers.DictField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
