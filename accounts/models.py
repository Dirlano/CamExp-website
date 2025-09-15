from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPES = (
        ('client', 'Client'),
        ('expert', 'Expert'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)  # For geolocation
    is_approved = models.BooleanField(default=False, help_text='Designates whether the expert account is approved.')
    
    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"
    
    class Meta:
        permissions = [
            ("can_approve_expert", "Can approve expert accounts"),
        ]