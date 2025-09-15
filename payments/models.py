from django.db import models
from accounts.models import Profile
from services.models import RequestPost

class Payment(models.Model):
    payer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='payments_made')
    payee = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='payments_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, completed, failed
    provider = models.CharField(max_length=20)  # mtn, orange
    transaction_id = models.CharField(max_length=100, blank=True)
    request = models.ForeignKey(RequestPost, on_delete=models.SET_NULL, null=True)