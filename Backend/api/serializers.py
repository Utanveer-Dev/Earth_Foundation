from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "country", "representation", "education_setting", "subjects", 
                  "age_group", "initiative", "worked_before", "state", "role", "date_of_birth", 
                  "in_full_time_secondary_school", "joining_again", "formed_team", "submitted_motivation_statement", 
                  "solution_complete", "exciting_statement", "created_at"]
         
    # Make fields optional for step-by-step saving
    # name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # email = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # country = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # representation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # role = serializers.ChoiceField(choices=Customer.ROLE_CHOICES, required=False)
