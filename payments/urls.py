from django.urls import path
from .views import (
    initiate_payment, 
    payment_status, 
    payment_callback,
    upload_payment_proof,
)

urlpatterns = [
    path('initiate/<int:request_id>/', initiate_payment, name='initiate_payment'),
    path('status/<int:payment_id>/', payment_status, name='payment_status'),
    path('callback/', payment_callback, name='payment_callback'),
    path('upload_proof/<int:payment_id>/', upload_payment_proof, name='upload_payment_proof'),
    
    # Provider-specific callbacks
    path('callback/mtn/', payment_callback, name='mtn_callback'),
    path('callback/orange/', payment_callback, name='orange_callback'),
    path('callback/card/', payment_callback, name='card_callback'),
]