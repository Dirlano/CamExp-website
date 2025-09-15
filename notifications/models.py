from django.db import models
from accounts.models import Profile

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('project_update', 'Project Update'),
        ('request_accepted', 'Request Accepted'),
        ('new_rating', 'New Rating'),
        ('new_reaction', 'New Reaction'),
        ('message', 'Message'),
        ('payment', 'Payment'),
        ('system', 'System'),
        ('service', 'Service'),
    )
    
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    message = models.TextField()
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system',
        help_text='Type of notification'
    )
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.message[:50]}"  
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])
            return True
        return False