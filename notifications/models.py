from django.db import models
from django.utils import timezone
from accounts.models import CustomUser

class Notification(models.Model):
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('project_update', 'Project Update'),
            ('message', 'Message'),
            ('payment', 'Payment'),
            ('rating', 'Rating'),
            ('system', 'System'),
            ('reminder', 'Reminder'),
            ('promotion', 'Promotion'),
            ('video_call', 'Video Call')
        ],
        default='system'
    )
    related_object_type = models.CharField(max_length=50, null=True, blank=True)  # ContentType
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
            return True
        return False

class NotificationPreference(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    notification_types = models.JSONField(default=dict)  # Granular preferences

    def __str__(self):
        return f"Preferences for {self.user.username}"