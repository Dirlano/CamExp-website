from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.views.generic import View, TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy

from .forms import RegistrationForm, ProfileForm, UserForm
from .models import Profile
from services.models import ServiceListing, RequestPost, Rating
from projects.models import Project, Event
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# In accounts/views.py, update the register view
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            logger.info("Form is valid. Creating user...")
            user = form.save(commit=False)
            user.save()
            logger.info(f"User created: {user.username}")
            
            # Create profile with user_type
            user_type = form.cleaned_data.get('user_type', 'client')
            logger.info(f"Creating profile with user_type: {user_type}")
            
            # Only require approval for experts
            is_approved = user_type != 'expert'  # Auto-approve non-experts
            profile = Profile(
                user=user, 
                user_type=user_type,
                is_approved=is_approved
            )
            profile.save()
            
            if user_type == 'expert':
                messages.success(
                    request,
                    'Your expert account has been created successfully! '
                    'Please wait for admin approval before logging in. You will receive an email once your account is approved.'
                )
                logger.info(f"Expert account {user.username} created, pending approval")
            else:
                messages.success(
                    request,
                    'Your account has been created successfully! Please log in to continue.'
                )
                logger.info(f"User {user.username} created successfully")
            
            return redirect('login')
        else:
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        # Check if the user has a profile
        if not hasattr(self.request.user, 'profile'):
            return reverse_lazy('home')
            
        # Redirect based on user type
        if self.request.user.profile.user_type == 'expert':
            return reverse_lazy('expert_dashboard')
        return reverse_lazy('client_dashboard')

@login_required
def profile(request):
    profile = request.user.profile
    
    # Get user's recent activities
    recent_services = []
    recent_requests = []
    
    if profile.user_type == 'expert':
        recent_services = ServiceListing.objects.filter(expert=profile).order_by('-created_at')[:5]
    else:
        recent_requests = RequestPost.objects.filter(client=profile).order_by('-created_at')[:5]
    
    # Get user's ratings if they're an expert
    ratings = []
    if profile.user_type == 'expert':
        ratings = Rating.objects.filter(expert=profile).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'recent_services': recent_services,
        'recent_requests': recent_requests,
        'ratings': ratings,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/change_password.html', context)

@login_required
def delete_account(request):
    if request.method == 'POST':
        # Confirm deletion
        if request.POST.get('confirm_delete') == 'true':
            user = request.user
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Please confirm account deletion.')
    
    return render(request, 'accounts/delete_account.html')

def user_profile(request, username):
    """Public profile view for other users"""
    try:
        user = User.objects.get(username=username)
        profile = user.profile
        
        # Get user's services if they're an expert
        services = []
        if profile.user_type == 'expert':
            services = ServiceListing.objects.filter(expert=profile).order_by('-created_at')[:6]
        
        # Get user's ratings if they're an expert
        ratings = []
        if profile.user_type == 'expert':
            ratings = Rating.objects.filter(expert=profile).order_by('-created_at')[:5]
        
        context = {
            'profile_user': user,
            'profile': profile,
            'services': services,
            'ratings': ratings,
        }
        return render(request, 'accounts/user_profile.html', context)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('home')

@login_required
def client_dashboard(request):
    """Dashboard view for clients"""
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'client':
        return redirect('home')
    
    # Get client's active service requests
    from services.models import RequestPost
    from projects.models import Project
    
    # Get active and completed projects
    active_requests = RequestPost.objects.filter(
        client=request.user.profile,
        status__in=['open', 'in_progress']
    ).order_by('-created_at')
    
    completed_requests = RequestPost.objects.filter(
        client=request.user.profile,
        status='completed'
    ).order_by('-created_at')[:5]
    
    # Get upcoming events for the client's projects
    from django.utils import timezone
    upcoming_events = []
    for req in active_requests:
        try:
            project = Project.objects.get(request=req)
            events = project.event_set.filter(start__gte=timezone.now()).order_by('start')[:3]
            upcoming_events.extend(events)
        except Project.DoesNotExist:
            pass
    
    # Sort events by start time and get top 3
    upcoming_events = sorted(upcoming_events, key=lambda x: x.start)[:3]
    
    context = {
        'user': request.user,
        'profile': request.user.profile,
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'upcoming_events': upcoming_events,
        'active_requests_count': active_requests.count(),
        'completed_requests_count': RequestPost.objects.filter(
            client=request.user.profile,
            status='completed'
        ).count(),
    }
    return render(request, 'dashboard/client_dashboard.html', context)

@login_required
def expert_dashboard(request):
    """Dashboard view for experts"""
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'expert':
        return redirect('home')
    
    from django.db.models import Avg, Count
    from services.models import Rating
    
    profile = request.user.profile
    
    # Active services
    active_services = ServiceListing.objects.filter(
        expert=profile,
        status='active'
    )
    
    # Active projects with related data
    active_projects = Project.objects.select_related('request').filter(
        request__accepted_expert=profile,
        status='in_progress'
    ).order_by('-created_at')
    
    # Upcoming events
    today = timezone.now().date()
    upcoming_events = Event.objects.select_related('project__request').filter(
        project__request__accepted_expert=profile,
        start__date__gte=today
    ).order_by('start')[:5]
    
    # Completed projects (last 5)
    completed_projects = Project.objects.select_related('request').filter(
        request__accepted_expert=profile,
        status='completed'
    ).order_by('-updated_at')[:5]
    
    # Total earnings from completed projects with budget
    completed_with_budget = Project.objects.select_related('request').filter(
        request__accepted_expert=profile,
        status='completed',
        request__budget__isnull=False
    )
    total_earnings = sum(
        project.request.budget for project in completed_with_budget
        if project.request.budget is not None
    )
    
    # Rating statistics from Rating model
    rating_stats = Rating.objects.filter(
        expert=profile
    ).aggregate(
        avg_rating=Avg('score'),
        rating_count=Count('id')
    )
    
    # Projects by status
    projects_by_status = Project.objects.filter(
        request__accepted_expert=profile
    ).values('status').annotate(
        count=Count('status')
    ).order_by('status')
    
    context = {
        'active_services': active_services,
        'services_count': active_services.count(),
        'active_projects': active_projects,
        'active_projects_count': active_projects.count(),
        'upcoming_events': upcoming_events,
        'completed_projects': completed_projects,
        'total_earnings': total_earnings or 0,
        'avg_rating': rating_stats['avg_rating'] or 0,
        'rating_count': rating_stats['rating_count'],
        'projects_by_status': projects_by_status,
        'active_tab': 'expert_dashboard',
    }
    
    return render(request, 'dashboard/expert_dashboard.html', context)