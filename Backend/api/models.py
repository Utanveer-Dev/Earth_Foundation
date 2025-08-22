from django.db import models 

class Customer(models.Model): 
    
    ROLE_CHOICES = [ 
                    ("teenager", "Teenager"), 
                    ("educator", "Educator"), 
                    ("adult", "Adult") ]  
    
    name = models.CharField(max_length=100, blank=True, null=True) 
    email = models.CharField(max_length=100, blank=True, null=True) 
    country = models.CharField(max_length=100, blank=True, null=True) 
    representation = models.TextField(blank=True, null=True) 
    
    education_setting = models.CharField(max_length=100, blank=True, null=True)
    subjects = models.CharField(max_length=100, blank=True, null=True)
    age_group = models.CharField(max_length=100, blank=True, null=True) 
    initiative = models.CharField(max_length=100, blank=True, null=True)
    worked_before = models.CharField(max_length=10, blank=True, null=True)
    
    date_of_birth = models.CharField(max_length=20, blank=True, null=True)
    in_full_time_secondary_school = models.CharField(max_length=10, blank=True, null=True)
    joining_again = models.CharField(max_length=20, blank=True, null=True) 
    formed_team = models.CharField(max_length=10, blank=True, null=True)
    submitted_motivation_statement = models.CharField(max_length=10, blank=True, null=True)
    solution_complete = models.CharField(max_length=10, blank=True, null=True)
    exciting_statement = models.CharField(max_length=100, blank=True, null=True)
    
    state = models.IntegerField(default=0) 
    role = models.CharField(max_length=20, choices=ROLE_CHOICES) 
    
    created_at = models.DateTimeField(auto_now_add=True) 
    
    def __str__(self): 
        return f"{self.name} ({self.role})"