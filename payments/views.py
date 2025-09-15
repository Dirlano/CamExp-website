import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
from services.models import RequestPost

# Add in settings.py: MTN_API_USER = '', MTN_API_KEY = '', MTN_BASE_URL = 'https://sandbox.momodeveloper.mtn.com' (change to prod)
# ORANGE_BASE_URL = 'https://api.orange.com', ORANGE_API_KEY = ''

@login_required
def initiate_payment(request, request_id):
    req = get_object_or_404(RequestPost, id=request_id)
    
    # Check if user is the client for this request
    if request.user.profile != req.client:
        messages.error(request, 'You can only pay for your own requests.')
        return redirect('service_detail', id=request_id)
    
    # Check if request is already paid
    existing_payment = Payment.objects.filter(request=req, status='completed').first()
    if existing_payment:
        messages.warning(request, 'This request has already been paid for.')
        return redirect('payment_status', payment_id=existing_payment.id)
    
    if request.method == 'POST':
        provider = request.POST.get('provider')
        payer_phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')
        
        if not provider or not payer_phone:
            messages.error(request, 'Please provide all required payment information.')
            return render(request, 'payments/initiate.html', {'request': req})
        
        # Create payment record
        payment = Payment.objects.create(
            payer=request.user.profile,
            payee=req.client,
            amount=req.budget,
            provider=provider,
            payment_method=payment_method,
            request=req,
            status='pending'
        )
        
        try:
            if provider == 'mtn':
                # MTN Mobile Money payment
                result = process_mtn_payment(payment, payer_phone)
                if result['success']:
                    payment.transaction_id = result['transaction_id']
                    payment.save()
                    messages.success(request, 'Payment initiated successfully! Please check your phone to approve the payment.')
                    return redirect('payment_status', payment_id=payment.id)
                else:
                    payment.status = 'failed'
                    payment.save()
                    messages.error(request, f'Payment failed: {result["message"]}')
                    
            elif provider == 'orange':
                # Orange Money payment
                result = process_orange_payment(payment, payer_phone)
                if result['success']:
                    payment.transaction_id = result['transaction_id']
                    payment.save()
                    messages.success(request, 'Payment initiated successfully! Please check your phone to approve the payment.')
                    return redirect('payment_status', payment_id=payment.id)
                else:
                    payment.status = 'failed'
                    payment.save()
                    messages.error(request, f'Payment failed: {result["message"]}')
                    
            elif provider == 'bank':
                # Bank transfer
                payment.status = 'pending'
                payment.save()
                messages.success(request, 'Bank transfer initiated. Please complete the transfer and upload proof.')
                return redirect('payment_status', payment_id=payment.id)
                
            elif provider == 'card':
                # Card payment (integrate with payment gateway)
                result = process_card_payment(payment, request.POST)
                if result['success']:
                    payment.status = 'completed'
                    payment.transaction_id = result['transaction_id']
                    payment.save()
                    messages.success(request, 'Payment completed successfully!')
                    return redirect('payment_status', payment_id=payment.id)
                else:
                    payment.status = 'failed'
                    payment.save()
                    messages.error(request, f'Card payment failed: {result["message"]}')
                    
        except Exception as e:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Payment processing error: {str(e)}')
    
    # Get available payment methods
    payment_methods = get_payment_methods()
    
    context = {
        'request': req,
        'payment_methods': payment_methods,
    }
    return render(request, 'payments/initiate.html', context)

def process_mtn_payment(payment, phone):
    """Process MTN Mobile Money payment"""
    try:
        # Get token
        token_response = requests.post(
            f'{getattr(settings, "MTN_BASE_URL", "https://sandbox.momodeveloper.mtn.com")}/collection/token/',
            auth=(getattr(settings, "MTN_API_USER", ""), getattr(settings, "MTN_API_KEY", "")),
            timeout=30
        )
        
        if token_response.status_code == 200:
            token = token_response.json().get('access_token')
            
            # Request to pay
            rtp_response = requests.post(
                f'{getattr(settings, "MTN_BASE_URL", "https://sandbox.momodeveloper.mtn.com")}/collection/v1_0/requesttopay',
                headers={
                    'Authorization': f'Bearer {token}',
                    'X-Reference-Id': str(payment.id),
                    'X-Target-Environment': 'sandbox',
                    'Content-Type': 'application/json'
                },
                json={
                    'amount': str(payment.amount),
                    'currency': 'XAF',
                    'externalId': str(payment.id),
                    'payer': {'partyIdType': 'MSISDN', 'partyId': phone},
                    'payerMessage': f'Payment for {payment.request.title}',
                    'payeeNote': 'CamExp payment'
                },
                timeout=30
            )
            
            if rtp_response.status_code == 202:
                return {
                    'success': True,
                    'transaction_id': rtp_response.headers.get('X-Reference-Id', str(payment.id))
                }
            else:
                return {
                    'success': False,
                    'message': f'MTN API error: {rtp_response.status_code}'
                }
        else:
            return {
                'success': False,
                'message': 'Failed to get MTN API token'
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }

def process_orange_payment(payment, phone):
    """Process Orange Money payment"""
    try:
        # Placeholder for Orange Money integration
        # You would implement the actual Orange Money API calls here
        return {
            'success': True,
            'transaction_id': f'ORANGE_{payment.id}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Orange Money error: {str(e)}'
        }

def process_card_payment(payment, post_data):
    """Process card payment"""
    try:
        # Placeholder for card payment gateway integration
        # You would integrate with Stripe, PayPal, or other payment gateways here
        return {
            'success': True,
            'transaction_id': f'CARD_{payment.id}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Card payment error: {str(e)}'
        }

def get_payment_methods():
    """Get available payment methods based on settings"""
    methods = []
    
    if hasattr(settings, 'MTN_API_USER') and settings.MTN_API_USER:
        methods.append({
            'id': 'mtn',
            'name': 'MTN Mobile Money',
            'icon': 'fa-solid fa-mobile-alt',
            'description': 'Pay with MTN Mobile Money'
        })
    
    if hasattr(settings, 'ORANGE_API_KEY') and settings.ORANGE_API_KEY:
        methods.append({
            'id': 'orange',
            'name': 'Orange Money',
            'icon': 'fa-solid fa-mobile-alt',
            'description': 'Pay with Orange Money'
        })
    
    # Always include bank and card options
    methods.extend([
        {
            'id': 'bank',
            'name': 'Bank Transfer',
            'icon': 'fa-solid fa-university',
            'description': 'Direct bank transfer'
        },
        {
            'id': 'card',
            'name': 'Credit/Debit Card',
            'icon': 'fa-solid fa-credit-card',
            'description': 'Pay with Visa, Mastercard, etc.'
        }
    ])
    
    return methods

@login_required
def payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Check if user has permission to view this payment
    if request.user.profile not in [payment.payer, payment.payee]:
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('home')
    
    # Update payment status if needed
    if payment.status == 'pending' and payment.provider in ['mtn', 'orange']:
        # Poll for status update
        updated_status = check_payment_status(payment)
        if updated_status != payment.status:
            payment.status = updated_status
            payment.save()
    
    context = {
        'payment': payment,
        'can_upload_proof': payment.status == 'pending' and payment.provider == 'bank' and request.user.profile == payment.payer,
    }
    return render(request, 'payments/status.html', context)

def check_payment_status(payment):
    """Check payment status from provider"""
    try:
        if payment.provider == 'mtn':
            # Check MTN payment status
            response = requests.get(
                f'{getattr(settings, "MTN_BASE_URL", "https://sandbox.momodeveloper.mtn.com")}/collection/v1_0/requesttopay/{payment.transaction_id}',
                headers={
                    'X-Target-Environment': 'sandbox',
                    'Authorization': f'Bearer {get_mtn_token()}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status == 'SUCCESSFUL':
                    return 'completed'
                elif status == 'FAILED':
                    return 'failed'
                else:
                    return 'pending'
                    
        elif payment.provider == 'orange':
            # Check Orange payment status
            # Implement Orange Money status check
            pass
            
    except Exception:
        pass
    
    return payment.status

def get_mtn_token():
    """Get MTN API token"""
    try:
        response = requests.post(
            f'{getattr(settings, "MTN_BASE_URL", "https://sandbox.momodeveloper.mtn.com")}/collection/token/',
            auth=(getattr(settings, "MTN_API_USER", ""), getattr(settings, "MTN_API_KEY", "")),
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception:
        pass
    
    return None

@login_required
def upload_payment_proof(request, payment_id):
    """Upload payment proof for bank transfers"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.user.profile != payment.payer:
        messages.error(request, 'You can only upload proof for your own payments.')
        return redirect('payment_status', payment_id=payment_id)
    
    if request.method == 'POST' and request.FILES.get('proof_file'):
        proof_file = request.FILES['proof_file']
        
        # Save proof file
        payment.proof_file = proof_file
        payment.status = 'pending_verification'
        payment.save()
        
        messages.success(request, 'Payment proof uploaded successfully. We will verify and update the status.')
        return redirect('payment_status', payment_id=payment_id)
    
    return redirect('payment_status', payment_id=payment_id)

@csrf_exempt
def payment_callback(request):
    """Handle webhook callbacks from payment providers"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Handle different provider callbacks
            if 'mtn' in request.path:
                return handle_mtn_callback(data)
            elif 'orange' in request.path:
                return handle_orange_callback(data)
            elif 'card' in request.path:
                return handle_card_callback(data)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def handle_mtn_callback(data):
    """Handle MTN payment callback"""
    try:
        reference_id = data.get('referenceId')
        status = data.get('status')
        
        if reference_id and status:
            payment = Payment.objects.filter(transaction_id=reference_id).first()
            if payment:
                if status == 'SUCCESSFUL':
                    payment.status = 'completed'
                elif status == 'FAILED':
                    payment.status = 'failed'
                payment.save()
                
                return JsonResponse({'status': 'success'})
    
    except Exception as e:
        pass
    
    return JsonResponse({'status': 'error'}, status=400)

def handle_orange_callback(data):
    """Handle Orange Money callback"""
    # Implement Orange Money callback handling
    return JsonResponse({'status': 'success'})

def handle_card_callback(data):
    """Handle card payment callback"""
    # Implement card payment callback handling
    return JsonResponse({'status': 'success'})