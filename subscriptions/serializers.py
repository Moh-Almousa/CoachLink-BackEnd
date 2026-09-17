# serializers.py for subscriptions app
from rest_framework import serializers
from .models import SubscriptionPackage

class SubscriptionPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPackage
        fields = ['id', 'name', 'number_month',
                  'price', 'description']
class SubscriptionPackagesSerializer(serializers.ModelSerializer):
    duration=serializers.IntegerField( source='number_month')
    class Meta:
        model = SubscriptionPackage
        fields = ['id', 'name','price', 'description','duration']

class CreatePaymentSerializer(serializers.Serializer):
    package_id = serializers.IntegerField()
