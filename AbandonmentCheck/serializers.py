from rest_framework import serializers
from .models import CheckoutStatus

class CheckoutStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutStatus
        fields = '__all__'
