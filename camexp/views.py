from django.shortcuts import render
from django.db.models import Avg
from services.models import ServiceListing, RequestPost, Rating
from accounts.models import Profile

def home(request):
    """Home page view with featured content"""
    # Get featured services
    featured_services = ServiceListing.objects.filter(is_featured=True).order_by('-created_at')[:6]
    
    # Get recent service requests
    recent_requests = RequestPost.objects.all().order_by('-created_at')[:6]
    
    # Get top experts (based on average rating)
    top_experts = Profile.objects.filter(user_type='expert').annotate(
        avg_rating=Avg('ratings_received__score')
    ).order_by('-avg_rating')[:4]
    
    # Get statistics
    total_services = ServiceListing.objects.count()
    total_requests = RequestPost.objects.count()
    total_experts = Profile.objects.filter(user_type='expert').count()
    total_clients = Profile.objects.filter(user_type='client').count()
    
    context = {
        'featured_services': featured_services,
        'recent_requests': recent_requests,
        'top_experts': top_experts,
        'total_services': total_services,
        'total_requests': total_requests,
        'total_experts': total_experts,
        'total_clients': total_clients,
    }
    
    return render(request, 'home.html', context)
