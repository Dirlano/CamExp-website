from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from projects.models import Project
import uuid

def generate_room_id():
    """Generate a Jitsi-friendly room ID without hyphens"""
    return str(uuid.uuid4()).replace('-', '')

class VideoCallSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]

    room_id = models.CharField(max_length=100, unique=True, default=generate_room_id)
    contract = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='video_calls')
    initiated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='initiated_calls')
    participants = models.ManyToManyField(CustomUser, related_name='video_call_sessions')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Video Call for {self.contract.title} - {self.room_id}"

    def end_call(self):
        self.status = 'ended'
        self.end_time = timezone.now()
        self.save()

    class Meta:
        ordering = ['-start_time']
