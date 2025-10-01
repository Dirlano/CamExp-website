from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('client', 'Client'),
        ('expert', 'Expert'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='client')
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_expert_approved = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    bio = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    class Meta:
        permissions = [
            ("can_approve_expert", "Can approve expert accounts"),
            ("can_create_video_call", "Can create video call sessions"),
        ]

    def save(self, *args, **kwargs):
        # Update coordinates when location changes
        if self.location and (not self.latitude or not self.longitude):
            from services.geolocation import GeolocationService
            GeolocationService.update_location_coordinates(self)
        super().save(*args, **kwargs)

    @property
    def is_expert(self):
        return self.user_type == 'expert'

    @property
    def is_client(self):
        return self.user_type == 'client'

# Keep Profile for backward compatibility during migration
class Profile(models.Model):
    USER_TYPES = (
        ('client', 'Client'),
        ('expert', 'Expert'),
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True, help_text='Comma-separated list of skills')
    is_approved = models.BooleanField(default=False, help_text='Designates whether the expert account is approved.')

    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"

    class Meta:
        permissions = [
            ("can_approve_expert", "Can approve expert accounts"),
        ]

    @classmethod
    def get_user_profile(cls, user):
        """Safely get or create user profile"""
        try:
            return user.profile
        except ObjectDoesNotExist:
            # Create profile if it doesn't exist
            return cls.objects.create(
                user=user,
                user_type='client',  # Default to client
                is_approved=True  # Auto-approve clients
            )