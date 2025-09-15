from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from .models import ServiceListing, RequestPost, Reaction, Rating
from accounts.models import Profile
from notifications.models import Notification
from .forms import ServiceForm, RequestForm, ReactionForm, RatingForm

def list_services(request):
    services = ServiceListing.objects.all().order_by('-created_at')
    categories = ServiceListing.objects.values_list('category', flat=True).distinct()
    
    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        services = services.filter(category=category)
    
    # Filter by location if provided
    location = request.GET.get('location')
    if location:
        services = services.filter(location__icontains=location)
    
    # Filter by price range if provided
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        services = services.filter(price__gte=min_price)
    if max_price:
        services = services.filter(price__lte=max_price)
    
    context = {
        'services': services,
        'categories': categories,
        'selected_category': category,
        'selected_location': location,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'services/list.html', context)

def search(request):
    query = request.POST.get('q') or request.GET.get('q')
    results = []
    if query:
        results = ServiceListing.objects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
            | Q(category__icontains=query)
        ).order_by('-created_at')
    return render(request, 'services/search.html', {'results': results, 'query': query})

@login_required
def create_listing(request):
    if request.user.profile.user_type != 'expert':
        messages.error(request, 'Only experts can create service listings.')
        return redirect('services:list')
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.expert = request.user.profile
            listing.save()
            messages.success(request, 'Service listing created successfully!')
            return redirect('services:service_detail', id=listing.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceForm()
    
    # Get categories and subcategories for the form
    categories = ServiceListing.objects.values_list('category', flat=True).distinct()
    
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'services/create_listing.html', context)

@login_required
def service_detail(request, id):
    service = get_object_or_404(ServiceListing, id=id)
    
    # Get related services by the same expert
    related_services = ServiceListing.objects.filter(
        expert=service.expert
    ).exclude(id=service.id)[:3]
    
    # Get ratings for this expert
    ratings = Rating.objects.filter(expert=service.expert).order_by('-created_at')[:5]
    
    # Check if user has already rated this expert
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(
            reviewer=request.user.profile,
            expert=service.expert
        ).first()
    
    context = {
        'service': service,
        'related_services': related_services,
        'ratings': ratings,
        'user_rating': user_rating,
    }
    return render(request, 'services/detail.html', context)

@login_required
def create_request(request):
    if request.user.profile.user_type != 'client':
        messages.error(request, 'Only clients can create service requests.')
        return redirect('services:list')
    
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.client = request.user.profile
            req.save()
            messages.success(request, 'Service request created successfully!')
            return redirect('services:service_detail', id=req.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RequestForm()
    
    context = {
        'form': form,
    }
    return render(request, 'services/create_request.html', context)

@login_required
def respond_request(request, id):
    req = get_object_or_404(RequestPost, id=id)
    
    # Check if user is an expert
    if request.user.profile.user_type != 'expert':
        messages.error(request, 'Only experts can respond to requests.')
        return redirect('services:service_detail', id=id)
    
    # Check if request is already accepted
    if req.status == 'accepted':
        messages.warning(request, 'This request has already been accepted.')
        return redirect('services:service_detail', id=id)
    
    if request.method == 'POST':
        # Handle the response form
        proposal_title = request.POST.get('proposal_title')
        executive_summary = request.POST.get('executive_summary')
        detailed_proposal = request.POST.get('detailed_proposal')
        proposed_amount = request.POST.get('proposed_amount')
        estimated_timeline = request.POST.get('estimated_timeline')
        deliverables = request.POST.get('deliverables')
        additional_services = request.POST.get('additional_services')
        why_choose_me = request.POST.get('why_choose_me')
        
        # Create a response (you might want to create a Response model for this)
        # For now, we'll update the request status
        req.status = 'accepted'
        req.accepted_expert = request.user.profile
        req.save()
        
        # Create notification
        Notification.objects.create(
            user=req.client,
            message=f'Your request "{req.title}" was accepted by {request.user.get_full_name()}',
            notification_type='request_accepted'
        )
        
        messages.success(request, 'Response submitted successfully!')
        return redirect('dashboard')
    
    context = {
        'request': req,
    }
    return render(request, 'services/respond.html', context)

@login_required
def rate_expert(request, expert_id):
    expert = get_object_or_404(Profile, id=expert_id)
    
    # Check if user has already rated this expert
    existing_rating = Rating.objects.filter(
        reviewer=request.user.profile,
        expert=expert
    ).first()
    
    if existing_rating:
        messages.warning(request, 'You have already rated this expert.')
        return redirect('services:service_detail', id=expert.id)
    
    if request.method == 'POST':
        # Handle the rating form
        rating_score = request.POST.get('rating')
        review_title = request.POST.get('review_title')
        review_content = request.POST.get('review_content')
        communication_rating = request.POST.get('communication_rating')
        quality_rating = request.POST.get('quality_rating')
        timeliness_rating = request.POST.get('timeliness_rating')
        value_rating = request.POST.get('value_rating')
        project_id = request.POST.get('project_id')
        anonymous = request.POST.get('anonymous') == 'on'
        
        # Create the rating
        rating = Rating.objects.create(
            reviewer=request.user.profile,
            expert=expert,
            score=rating_score,
            review=review_content,
            review_title=review_title,
            communication_rating=communication_rating or 0,
            quality_rating=quality_rating or 0,
            timeliness_rating=timeliness_rating or 0,
            value_rating=value_rating or 0,
            anonymous=anonymous
        )
        
        # Create notification
        Notification.objects.create(
            user=expert,
            message=f'You received a new rating from {request.user.get_full_name()}',
            notification_type='new_rating'
        )
        
        messages.success(request, 'Rating submitted successfully!')
        return redirect('services:service_detail', id=expert.id)
    
    # Get user's projects for optional linking
    user_projects = []
    if hasattr(request.user, 'profile'):
        # You might need to adjust this based on your Project model
        pass
    
    context = {
        'expert': expert,
        'user_projects': user_projects,
    }
    return render(request, 'services/rate.html', context)

@login_required
def react_post(request, post_id):
    post = get_object_or_404(ServiceListing, id=post_id)
    
    if request.method == 'POST':
        form = ReactionForm(request.POST)
        if form.is_valid():
            reaction = form.save(commit=False)
            reaction.user = request.user.profile
            reaction.post = post
            reaction.save()
            
            # Create notification
            Notification.objects.create(
                user=post.expert,
                message=f'{request.user.get_full_name()} reacted to your service listing',
                notification_type='new_reaction'
            )
            
            messages.success(request, 'Reaction added successfully!')
            return redirect('services:service_detail', id=post_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReactionForm()
    
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'services/react.html', context)

# API views for AJAX requests
@login_required
def get_subcategories(request):
    """Get subcategories for a given category"""
    category = request.GET.get('category')
    if category:
        # You can implement subcategory logic here
        subcategories = []  # Placeholder
        return JsonResponse({'subcategories': subcategories})
    return JsonResponse({'subcategories': []})

@login_required
def toggle_favorite(request, service_id):
    """Toggle favorite status for a service"""
    service = get_object_or_404(ServiceListing, id=service_id)
    # Implement favorite logic here
    return JsonResponse({'status': 'success'})