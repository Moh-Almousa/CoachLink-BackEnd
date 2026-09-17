from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.
def validate_email(value):
    if not value.endswith('@gmail.com'):
        raise ValidationError('Email must be a Gmail address.')

class User(AbstractBaseUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        COACH = 'coach', 'Coach'
        PLAYER = 'player', 'Player'

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'

    class AuthProvider(models.TextChoices):
        LOCAL = 'local', 'Local'
        GOOGLE = 'google', 'Google'

    full_name = models.CharField(max_length=250)
    email = models.CharField(max_length=100, unique=True, validators=[validate_email])
    password = models.CharField(
        max_length=250, null=True, blank=True, db_column='password'
    )
    role = models.CharField(
        max_length=10, choices=Role.choices, 
        null=True, blank=True, db_column='rol'
    )
    gender = models.CharField(
        max_length=10, choices=Gender.choices, null=True, blank=True
    )
    birth_date = models.DateField(null=True, blank=True)

    auth_provider = models.CharField(
        max_length=50, choices=AuthProvider.choices,
        default=AuthProvider.LOCAL, null=True, blank=True
    )
    provider_user_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=False,db_column='status')
    created_at = models.DateTimeField(
        default=timezone.now, null=True, blank=True, db_column='creat_at'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    class Meta:
        db_table = 'Users'

    def __str__(self):
        return f'{self.full_name}  ({self.email})'


class Otp(models.Model):
    def is_expired(self):
        return timezone.now() > self.expires_at
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, db_column='user_id',
        related_name='otps'
    )
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'Otps'


class CoachProfile(models.Model):
    class VerificationStatus(models.TextChoices):
            WAITING = 'waiting', 'Waiting'
            ACCEPTED = 'accepted', 'Accepted'
            REJECTED = 'rejected', 'Rejected'
    class Specialization(models.TextChoices):
        BODYBUILDING = 'Bodybuilding', 'Bodybuilding' 
        POWERLIFTING = 'PowerLifting', 'PowerLifting'
        BOTH = 'Both', 'Both'

    
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, db_column='user_id',
        related_name='coach_profile'
    )
    specialization = models.CharField(
        max_length=50, choices=Specialization.choices, null=True, blank=True
    )
    experience_years = models.PositiveSmallIntegerField(null=True, blank=True)
    bio = models.CharField(max_length=500, null=True, blank=True)
    image_profile_url = models.ImageField(upload_to='profiles/', null=True, blank=True)
    verification_status = models.CharField(
        max_length=50, choices=VerificationStatus.choices, null=True, blank=True
    )
    instagram_url = models.CharField(max_length=255, null=True, blank=True)
    facebook_url = models.CharField(max_length=255, null=True, blank=True)
    whatsapp_url = models.CharField(max_length=255, null=True, blank=True)
    youtube_url = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,db_column='update_at')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'Coach_Profiles'

    def __str__(self):
        return f'Coach #{self.pk} - {self.user}'


class Certificate(models.Model):
    class VerificationStatus(models.TextChoices):
        WAITING = 'waiting', 'Waiting'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
    class RejectionReason(models.TextChoices):
        SERIAL = 'Certificate photo is unclear / Serial number not visible', 'Certificate photo is unclear / Serial number not visible'
        INVALID_CREDENTIALS = 'Invalid or forged credentials', 'Invalid or forged credentials'
        OTHER = 'Other', 'Other'
    coach_profile = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='certificates')
    reviewed_by = models.ForeignKey(
User,on_delete=models.SET_NULL,null=True,blank=True,related_name="reviewed_verifications"
    )
    certificate_pdf_url = models.FileField(upload_to='certificates/', null=True, blank=True)
    verification_status = models.CharField(
        max_length=50, choices=VerificationStatus.choices, null=True, blank=True
    )
    rejection_reason = models.CharField(max_length=500, choices=RejectionReason.choices, null=True, blank=True)
    note = models.CharField(max_length=500, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


class PlayerProfile(models.Model):
    class Goal(models.TextChoices):
        MUSCLE_BUILDING = 'Muscle Building', 'Muscle Building'
        WEIGHT_LOSS = 'Weight Loss', 'Weight Loss'
        GENERAL_HEALTH = 'General Health', 'General Health'

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, db_column='user_id',
        related_name='player_profile'
    )
    training_age_years = models.PositiveSmallIntegerField(null=True, blank=True)
    image_profile_url = models.ImageField(upload_to='profiles/', null=True, blank=True)
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(1)],
    )
    goal = models.CharField(
        max_length=100, choices=Goal.choices, null=True, blank=True
    )
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    is_injury = models.BooleanField(null=True, blank=True)
    note_injury = models.CharField(max_length=500, null=True, blank=True)
    note_sick = models.CharField(max_length=500, null=True, blank=True)
    bio = models.CharField(max_length=500, null=True, blank=True)
    weight_goal_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(1)],
    )
    updated_at = models.DateTimeField(auto_now=True, db_column='update_at')

    class Meta:
        db_table = 'Player_Profiles'

    def __str__(self):
        return f'Player #{self.pk} - {self.user}'


class AdminProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.PROTECT, null=True, blank=True,
        db_column='user_id', related_name='admin_profile'
    )
    class Meta:
        db_table = 'Admin_Profiles'


class CoachTransformation(models.Model):
    coach = models.ForeignKey(
        CoachProfile, on_delete=models.CASCADE, db_column='coach_id',
        related_name='transformations'
    )
    before_image_url = models.ImageField(upload_to='coach_album/')
    after_image_url = models.ImageField(upload_to='coach_album/')
    duration = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Coach_Transformations'

    def __str__(self):
        return f'Transformation #{self.pk} - {self.coach}'


class CoachRating(models.Model):
    coach = models.ForeignKey(
        CoachProfile, on_delete=models.PROTECT, db_column='coach_id',
        related_name='ratings'
    )
    player = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT,
                               db_column='player_id',related_name='given_ratings')
    rating = models.PositiveSmallIntegerField(validators=[ 
                                            MinValueValidator(1),
                                            MaxValueValidator(5)]
                                            )
    created_at = models.DateTimeField( default=timezone.now, null=True, blank=True, db_column='creat_at')
    class Meta:
        db_table = 'Coach_ratings'
        constraints = [
            models.UniqueConstraint(fields=['coach','player'], name='uq_coachrating_coach_player')
        ]
