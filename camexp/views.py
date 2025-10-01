from django.shortcuts import render, redirect
from django.db.models import Avg
from services.models import Service, ServiceRequest, Rating
from accounts.models import CustomUser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import sys
import traceback

from django.db.models import Count, Q

def home(request):
    """Home page view with featured content"""
    # Get featured services
    featured_services = Service.objects.filter(is_active=True).order_by('-created_at')[:6]

    # Get recent service requests
    recent_requests = ServiceRequest.objects.all().order_by('-created_at')[:6]

    # Get top experts (based on average rating)
    top_experts = CustomUser.objects.filter(user_type='expert').annotate(
        avg_rating=Avg('ratings_received__overall_rating')
    ).order_by('-avg_rating')[:4]

    # Get popular services based on count of 'like' reactions
    popular_services = Service.objects.filter(is_active=True).annotate(
        like_count=Count('reactions', filter=Q(reactions__type='like'))
    ).order_by('-like_count')[:6]

    # Get statistics
    total_services = Service.objects.count()
    total_requests = ServiceRequest.objects.count()
    total_experts = CustomUser.objects.filter(user_type='expert').count()
    total_clients = CustomUser.objects.filter(user_type='client').count()

    context = {
        'featured_services': featured_services,
        'recent_requests': recent_requests,
        'top_experts': top_experts,
        'popular_services': popular_services,
        'total_services': total_services,
        'total_requests': total_requests,
        'total_experts': total_experts,
        'total_clients': total_clients,
    }

    return render(request, 'home.html', context)


def custom_error_view(request, exception=None):
    """Custom 500 error view that shows error details"""
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # Get the traceback as a string
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    context = {
        'error_type': exc_type.__name__ if exc_type else 'Unknown Error',
        'error_message': str(exc_value) if exc_value else 'An unexpected error occurred',
        'traceback': tb_str,
        'request_path': request.path,
        'request_method': request.method,
    }

    return render(request, '500.html', context, status=500)


@login_required
def admin_initiate_call(request):
    """Admin interface for initiating video calls"""
    # Allow access if user is staff (Django admin) OR has user_type='admin'
    if not (request.user.is_staff or request.user.user_type == 'admin'):
        from django.contrib import messages
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('admin:index')

    from projects.models import Project
    projects = Project.objects.filter(client__isnull=False, expert__isnull=False)
    return render(request, 'admin/video_call_initiator.html', {'projects': projects})


@login_required
def video_call_room(request, room_identifier):
    """Video call room view"""
    from video_calls.models import VideoCallSession

    # Try to find the call by ID first (integer), then by room_id (UUID)
    call = None
    try:
        # Try parsing as integer (session ID)
        session_id = int(room_identifier)
        call = VideoCallSession.objects.get(id=session_id, participants=request.user)
    except (ValueError, VideoCallSession.DoesNotExist):
        # Try as room_id (UUID string)
        try:
            call = VideoCallSession.objects.get(room_id=room_identifier, participants=request.user)
        except VideoCallSession.DoesNotExist:
            pass

    if call:
        is_admin = request.user == call.initiated_by
        return render(request, 'video_call_room.html', {
            'room_id': call.room_id,
            'call': call,
            'is_admin': is_admin,
            'user_name': request.user.get_full_name() or request.user.username
        })
    else:
        messages.error(request, 'You do not have access to this video call.')
        return redirect('notifications:list')
