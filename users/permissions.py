from rest_framework.permissions import BasePermission
from .models import User , CoachProfile , PlayerProfile
from subscriptions.models import SubscriptionPlayer
class IsPlayer(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.PLAYER
        )

class IsCoach(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.COACH
        )

class IsVerifiedCoach(BasePermission):
    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.role == User.Role.COACH):
            return False
        coach_profile = getattr(request.user, 'coach_profile', None)
        if coach_profile is None:
            return False
        return coach_profile.verification_status == CoachProfile.VerificationStatus.ACCEPTED

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )

class IsActivePlayerOfCoach(BasePermission):
    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.role == User.Role.PLAYER):
            return False
        coachId=request.data.get('coachId')
        if not coachId :
            return False
        return (SubscriptionPlayer.objects.filter(
            player=request.user.player_profile,
            package__coach=request.data.get('coachId'),
            status=SubscriptionPlayer.Status.ACTIVE
        ).exists())

