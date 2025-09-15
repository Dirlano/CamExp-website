from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Project, Event
from services.models import RequestPost, ServiceListing
from accounts.models import Profile
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

@login_required
def dashboard(request):
    """Enhanced dashboard with statistics and project management"""
    # Get or create profile if it doesn't exist
    profile, created = Profile.objects.get_or_create(user=request.user)
    if created:
        # Set default values for new profile
        profile.user_type = 'client'  # or any default user type you prefer
        profile.save()
    
    if profile.user_type == 'client':
        # Client dashboard
        projects = Project.objects.filter(request__client=profile).order_by('-created_at')
        requests = RequestPost.objects.filter(client=profile).order_by('-created_at')
        
        # Statistics
        total_projects = projects.count()
        completed_projects = projects.filter(status='completed').count()
        active_projects = projects.filter(status='in_progress').count()
        total_spent = sum(project.request.budget for project in projects if project.status == 'completed')
        
        # Recent activities
        recent_activities = get_client_activities(profile)
        
        # Upcoming deadlines
        upcoming_deadlines = get_upcoming_deadlines(projects)
        
        # Common statistics
        total_requests = RequestPost.objects.count()
        total_services = ServiceListing.objects.count()
        total_users = Profile.objects.count()
        
        # Project status distribution for charts
        project_status_data = get_project_status_data(projects)
        
        # Monthly progress data
        monthly_progress = get_monthly_progress_data(projects)
        
        # Quick actions
        quick_actions = get_quick_actions(profile)
        
        context = {
            'profile': profile,
            'projects': projects[:10],  # Show only recent projects
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'active_projects': active_projects,
            'total_requests': total_requests,
            'total_services': total_services,
            'total_users': total_users,
            'recent_activities': recent_activities,
            'upcoming_deadlines': upcoming_deadlines,
            'project_status_data': project_status_data,
            'monthly_progress': monthly_progress,
            'quick_actions': quick_actions,
        }
        
        # Add user-specific data
        context.update({
            'total_spent': total_spent,
            'requests': requests[:5],
        })
        
        return render(request, 'projects/client_dashboard.html', context)
    
    else:  # expert dashboard
        # Expert dashboard
        projects = Project.objects.filter(request__accepted_expert=profile).order_by('-created_at')
        services = ServiceListing.objects.filter(expert=profile).order_by('-created_at')
        
        # Statistics
        total_projects = projects.count()
        completed_projects = projects.filter(status='completed').count()
        active_projects = projects.filter(status='in_progress').count()
        total_earned = sum(project.request.budget for project in projects if project.status == 'completed')
        
        # Get pending tasks (assuming you have a Task model with a status field)
        try:
            from tasks.models import Task
            pending_tasks = Task.objects.filter(
                Q(assigned_to=profile) & 
                ~Q(status='completed') & 
                ~Q(status='cancelled')
            ).count()
        except ImportError:
            pending_tasks = 0  # Fallback if tasks app is not available
        
        # Recent activities
        recent_activities = get_expert_activities(profile)[:5]  # Limit to 5 most recent
        
        # Upcoming deadlines (next 7 days)
        upcoming_tasks = []
        if 'tasks' in locals():
            upcoming_tasks = Task.objects.filter(
                assigned_to=profile,
                due_date__gte=timezone.now(),
                due_date__lte=timezone.now() + timezone.timedelta(days=7)
            ).order_by('due_date')[:5]
        
        # Recent projects (last 5)
        recent_projects = projects[:5]
        
        context = {
            # Dashboard stats
            'active_projects_count': active_projects,
            'completed_projects_count': completed_projects,
            'pending_tasks_count': pending_tasks,
            'total_earnings': total_earned,
            
            # Recent items
            'recent_projects': recent_projects,
            'upcoming_tasks': upcoming_tasks,
            'recent_activities': recent_activities,
            
            # Additional context
            'profile': profile,
            'services': services[:5],
            'total_requests': RequestPost.objects.count(),
            'total_services': ServiceListing.objects.count(),
            'total_users': Profile.objects.count(),
            'project_status_data': get_project_status_data(projects),
            'monthly_progress': get_monthly_progress_data(projects),
            'quick_actions': get_quick_actions(profile),
        }
        
        return render(request, 'projects/expert_dashboard.html', context)

@login_required
def schedule(request, project_id):
    """Project schedule and timeline management"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to this project
    if request.user.profile not in [project.request.client, project.request.accepted_expert]:
        messages.error(request, 'You do not have access to this project.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Handle event creation/updates
        event_title = request.POST.get('event_title')
        event_date = request.POST.get('event_date')
        event_description = request.POST.get('event_description')
        event_type = request.POST.get('event_type')
        
        if event_title and event_date:
            Event.objects.create(
                project=project,
                title=event_title,
                date=event_date,
                description=event_description,
                event_type=event_type or 'milestone'
            )
            messages.success(request, 'Event added successfully!')
            return redirect('schedule', project_id=project_id)
    
    # Get project events
    events = Event.objects.filter(project=project).order_by('date')
    
    # Group events by month for calendar view
    events_by_month = {}
    for event in events:
        month_key = event.date.strftime('%Y-%m')
        if month_key not in events_by_month:
            events_by_month[month_key] = []
        events_by_month[month_key].append(event)
    
    context = {
        'project': project,
        'events': events,
        'events_by_month': events_by_month,
    }
    return render(request, 'projects/schedule.html', context)

@login_required
def project_detail(request, project_id):
    """Detailed project view"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to this project
    if request.user.profile not in [project.request.client, project.request.accepted_expert]:
        messages.error(request, 'You do not have access to this project.')
        return redirect('dashboard')
    
    # Get project events
    events = Event.objects.filter(project=project).order_by('date')
    
    # Get project files/deliverables
    project_files = []  # You can implement file management here
    
    context = {
        'project': project,
        'events': events,
        'project_files': project_files,
    }
    return render(request, 'projects/detail.html', context)

@login_required
def create_project(request, request_id):
    """Create a new project from a service request"""
    service_request = get_object_or_404(RequestPost, id=request_id)
    
    # Check if user is the client
    if request.user.profile != service_request.client:
        messages.error(request, 'You can only create projects from your own requests.')
        return redirect('service_detail', id=request_id)
    
    # Check if project already exists
    if Project.objects.filter(request=service_request).exists():
        messages.warning(request, 'A project already exists for this request.')
        return redirect('project_detail', project_id=Project.objects.get(request=service_request).id)
    
    if request.method == 'POST':
        project_title = request.POST.get('project_title')
        project_description = request.POST.get('project_description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if project_title and start_date:
            project = Project.objects.create(
                request=service_request,
                title=project_title,
                description=project_description or service_request.description,
                start_date=start_date,
                end_date=end_date,
                status='planning'
            )
            
            messages.success(request, 'Project created successfully!')
            return redirect('project_detail', project_id=project.id)
        else:
            messages.error(request, 'Please provide all required information.')
    
    context = {
        'service_request': service_request,
    }
    return render(request, 'projects/create.html', context)

@login_required
def update_project_status(request, project_id):
    """Update project status"""
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        new_status = request.POST.get('status')
        
        # Check if user has permission to update
        if request.user.profile != project.request.accepted_expert:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        if new_status in ['planning', 'in_progress', 'review', 'completed', 'on_hold']:
            project.status = new_status
            project.save()
            
            # Create notification for client
            from notifications.views import create_notification
            create_notification(
                user=project.request.client,
                message=f'Project "{project.title}" status updated to {new_status}',
                notification_type='project_update',
                related_object=project
            )
            
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def expert_projects(request):
    """View all projects for the expert"""
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'expert':
        return redirect('home')
    
    projects = Project.objects.filter(
        request__accepted_expert=request.user.profile
    ).order_by('-created_at')
    
    context = {
        'projects': projects,
        'active_tab': 'expert_projects',
        'title': 'My Projects',
    }
    return render(request, 'projects/expert_projects.html', context)

@login_required
def completed_projects(request):
    """View all completed projects for the expert"""
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'expert':
        return redirect('home')
    
    projects = Project.objects.filter(
        request__accepted_expert=request.user.profile,
        status='completed'
    ).order_by('-completed_date')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(projects, 10)  # Show 10 projects per page
    
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
    
    context = {
        'projects': projects,
        'active_tab': 'completed_projects',
        'title': 'Completed Projects',
    }
    return render(request, 'projects/completed_projects.html', context)

# Helper functions
def get_client_activities(profile):
    """Get recent activities for a client"""
    activities = []
    
    # Recent requests
    recent_requests = RequestPost.objects.filter(client=profile).order_by('-created_at')[:5]
    for req in recent_requests:
        activities.append({
            'type': 'request_created',
            'title': f'Created request: {req.title}',
            'date': req.created_at,
            'object': req
        })
    
    # Recent project updates
    recent_projects = Project.objects.filter(request__client=profile).order_by('-updated_at')[:5]
    for project in recent_projects:
        activities.append({
            'type': 'project_update',
            'title': f'Project updated: {project.title}',
            'date': project.updated_at,
            'object': project
        })
    
    # Sort by date
    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:10]

def get_expert_activities(profile):
    """Get recent activities for an expert"""
    activities = []
    
    # Recent service listings
    recent_services = ServiceListing.objects.filter(expert=profile).order_by('-created_at')[:5]
    for service in recent_services:
        activities.append({
            'type': 'service_created',
            'title': f'Created service: {service.title}',
            'date': service.created_at,
            'object': service
        })
    
    # Recent project updates
    recent_projects = Project.objects.filter(request__accepted_expert=profile).order_by('-updated_at')[:5]
    for project in recent_projects:
        activities.append({
            'type': 'project_update',
            'title': f'Project updated: {project.title}',
            'date': project.updated_at,
            'object': project
        })
    
    # Sort by date
    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:10]

def get_upcoming_deadlines(projects):
    """Get upcoming project deadlines"""
    upcoming = []
    today = timezone.now().date()
    
    for project in projects:
        if project.end_date and project.end_date >= today:
            days_remaining = (project.end_date - today).days
            if days_remaining <= 7:  # Show deadlines within a week
                upcoming.append({
                    'project': project,
                    'days_remaining': days_remaining,
                    'is_urgent': days_remaining <= 3
                })
    
    # Sort by urgency
    upcoming.sort(key=lambda x: x['days_remaining'])
    return upcoming[:5]

def get_project_status_data(projects):
    """Get project status distribution for charts"""
    status_counts = projects.values('status').annotate(count=Count('status'))
    
    # Define status colors
    status_colors = {
        'planning': '#3B82F6',      # Blue
        'in_progress': '#F59E0B',   # Yellow
        'review': '#8B5CF6',        # Purple
        'completed': '#10B981',     # Green
        'on_hold': '#EF4444',       # Red
    }
    
    data = []
    for status_count in status_counts:
        status = status_count['status']
        count = status_count['count']
        if count > 0:
            data.append({
                'label': status.replace('_', ' ').title(),
                'value': count,
                'color': status_colors.get(status, '#6B7280')
            })
    
    return data

def get_monthly_progress_data(projects):
    """Get monthly project progress data"""
    monthly_data = []
    
    # Get last 6 months
    for i in range(6):
        date = timezone.now().date() - timedelta(days=30*i)
        month_key = date.strftime('%Y-%m')
        
        # Count projects created in this month
        month_projects = projects.filter(created_at__year=date.year, created_at__month=date.month)
        completed_count = month_projects.filter(status='completed').count()
        total_count = month_projects.count()
        
        monthly_data.append({
            'month': date.strftime('%b %Y'),
            'completed': completed_count,
            'total': total_count,
            'completion_rate': (completed_count / total_count * 100) if total_count > 0 else 0
        })
    
    return list(reversed(monthly_data))

def get_quick_actions(profile):
    """Get quick actions based on user type"""
    if profile.user_type == 'client':
        return [
            {
                'title': 'Create Request',
                'description': 'Post a new service request',
                'icon': 'fa-solid fa-plus',
                'url': 'create_request',
                'color': 'bg-primary'
            },
            {
                'title': 'View Projects',
                'description': 'Check your active projects',
                'icon': 'fa-solid fa-project-diagram',
                'url': 'dashboard',
                'color': 'bg-success'
            },
            {
                'title': 'Browse Services',
                'description': 'Find experts and services',
                'icon': 'fa-solid fa-search',
                'url': 'services:list',
                'color': 'bg-info'
            }
        ]
    else:
        return [
            {
                'title': 'Create Service',
                'description': 'Add a new service listing',
                'icon': 'fa-solid fa-plus',
                'url': 'create_listing',
                'color': 'bg-primary'
            },
            {
                'title': 'View Projects',
                'description': 'Manage your active projects',
                'icon': 'fa-solid fa-project-diagram',
                'url': 'dashboard',
                'color': 'bg-success'
            },
            {
                'title': 'Browse Requests',
                'description': 'Find new project opportunities',
                'icon': 'fa-solid fa-search',
                'url': 'services:list',
                'color': 'bg-info'
            }
        ]