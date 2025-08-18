from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "country", "representation", "state", "role", "created_at"]

    # Make fields optional for step-by-step saving
    # name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # email = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # country = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # representation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # role = serializers.ChoiceField(choices=Customer.ROLE_CHOICES, required=False)
