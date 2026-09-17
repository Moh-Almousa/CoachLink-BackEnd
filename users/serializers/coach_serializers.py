from rest_framework import serializers
from ..models import ( CoachProfile, CoachTransformation, CoachRating ,
                      Certificate )
from django.utils import timezone
from subscriptions.serializers import SubscriptionPackagesSerializer
from subscriptions.models import SubscriptionPlayer

#==== لرفع شهادات المدرب =====
class CoachCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['certificate_pdf_url']
        
#==== لعمل بيانات المهنة للمدرب =====
class CoachProfessionalInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachProfile
        fields = ['specialization', 'experience_years', 'bio', 'image_profile_url',
                  'instagram_url','facebook_url','whatsapp_url','youtube_url']

#==== لعرض بيانات المدرب =====
class CoachProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    birth_date = serializers.DateField(source="user.birth_date", read_only=True)
    age= serializers.SerializerMethodField()
    class Meta:
        model = CoachProfile
        fields = ['id','full_name','email','birth_date','age','specialization','experience_years',
            'bio','image_profile_url','verification_status','instagram_url','facebook_url','youtube_url','whatsapp_url',]
    def get_age(self, obj):
        if obj.user.birth_date:
            today = timezone.now().date()
            age = today.year - obj.user.birth_date.year - (
                (today.month, today.day) < (obj.user.birth_date.month,
                                            obj.user.birth_date.day))
            return age
        return None


class CoachRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachRating
        fields = ['id', 'coach', 'player', 'rating', 'created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'player': {'read_only': True},
            'created_at': {'read_only': True},
        }


class CoachCardSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    avr_rating = serializers.SerializerMethodField()
    Reviews = serializers.IntegerField(read_only=True)
    totalplayer = serializers.IntegerField(read_only=True)
    class Meta:
        model = CoachProfile
        fields = ['id', 'full_name', 'specialization', 'experience_years',
                  'avr_rating', 'Reviews', 'totalplayer',
                  'image_profile_url', 'created_at']
    def get_avr_rating(self, obj):
        return round(obj.avr_rating, 1) if obj.avr_rating is not None else 0


class CoachCertificateDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['id', 'certificate_pdf_url', 'verification_status', 'rejection_reason', 'verified_at']

#==== لإضافة/عرض صور قبل وبعد للمدرب =====
class CoachTransformationSerializer(serializers.ModelSerializer):
    before= serializers.ImageField(source='before_image_url')
    after= serializers.ImageField(source='after_image_url')
    class Meta:
        model = CoachTransformation
        fields = ['id', 'before', 'after', 'duration', 'created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }


#==== لعرض قائمة تقييمات المدرب الفردية (اسم اللاعب + صورته + التقييم) =====
# CoachRating ما عندو حقل تعليق نصي أصلاً (انلغى من الفرونت من الأساس)،
# فهاد بس رقم التقييم + هوية اللاعب يلي قيّم.
class CoachRatingWithPlayerSerializer(serializers.ModelSerializer):
    playerName = serializers.CharField(source="player.user.full_name", read_only=True)
    playerImage = serializers.ImageField(source="player.image_profile_url", read_only=True)
    class Meta:
        model = CoachRating
        fields = ['id', 'playerName', 'playerImage', 'rating', 'created_at']


class CoachDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    avr_rating = serializers.SerializerMethodField()
    Reviews = serializers.IntegerField(read_only=True)
    totalplayer = serializers.IntegerField(read_only=True)
    transformations = CoachTransformationSerializer(many=True, read_only=True)
    packages = SubscriptionPackagesSerializer(many=True, read_only=True)
    ratings = CoachRatingWithPlayerSerializer(many=True, read_only=True)
    class Meta:
        model = CoachProfile
        fields = ['id', 'full_name', 'specialization', 'bio', 'avr_rating',
                  'Reviews', 'totalplayer', 'image_profile_url',
                  'transformations', 'packages', 'ratings']
    def get_avr_rating(self, obj):
        return round(obj.avr_rating, 1) if obj.avr_rating is not None else 0
    
    
class PlayerInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Player email is required.")
        return value.lower().strip()

class CoachDashboardSerializer(serializers.Serializer):
    full_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    totalplayer= serializers.IntegerField()
    activeplayer= serializers.IntegerField()
    expiring_soon = serializers.IntegerField()
    revenue= serializers.DecimalField(max_digits=10, decimal_places=2)
    recent_activity = serializers.ListField()
    
class CoachPlayersStatsSerializer(serializers.Serializer):
    totalplayer= serializers.IntegerField()
    activeplayer= serializers.IntegerField()
    new_players_this_month = serializers.IntegerField()
    expired_subscriptions = serializers.IntegerField()

class CoachPlayerCardSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="player.user.full_name", read_only=True)
    goal = serializers.CharField(source="player.goal", read_only=True)
    image_profile_url =serializers.ImageField(source="player.image_profile_url", read_only=True)
    # user_id (User.id الحقيقي، مختلف عن player=PlayerProfile.id) - لازم
    # لشاشة المراسلة (SendMessageView.receiver_id بده User.id مش PlayerProfile.id)
    user_id = serializers.IntegerField(source="player.user_id", read_only=True)
    class Meta:
        model = SubscriptionPlayer
        fields = ['player','user_id','image_profile_url', 'full_name','goal','start_date','end_date','status']
    