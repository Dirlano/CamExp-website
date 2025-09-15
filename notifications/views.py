from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification

@login_required
def list_notifications(request):
    """Display user's notifications with filtering and pagination"""
    notifications = Notification.objects.filter(user=request.user.profile).order_by('-timestamp')
    
    # Filter by read status if provided
    read_status = request.GET.get('read')
    if read_status == 'unread':
        notifications = notifications.filter(read=False)
    elif read_status == 'read':
        notifications = notifications.filter(read=True)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 20)  # 20 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get notification counts
    total_count = notifications.count()
    unread_count = notifications.filter(read=False).count()
    read_count = total_count - unread_count
    
    context = {
        'notifications': page_obj,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
    }
    
    return render(request, 'notifications/list.html', context)

@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user.profile
        )
        notification.read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

@login_required
@require_POST
def mark_all_as_read(request):
    """Mark all user's notifications as read"""
    try:
        Notification.objects.filter(
            user=request.user.profile,
            read=False
        ).update(read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a specific notification"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user.profile
        )
        notification.delete()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

@login_required
@require_POST
def clear_all_notifications(request):
    """Clear all user's notifications"""
    try:
        Notification.objects.filter(user=request.user.profile).delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def notification_settings(request):
    """User notification preferences"""
    if request.method == 'POST':
        # Handle notification preference updates
        email_notifications = request.POST.get('email_notifications') == 'on'
        push_notifications = request.POST.get('push_notifications') == 'on'
        sms_notifications = request.POST.get('sms_notifications') == 'on'
        
        # Update user profile notification preferences
        profile = request.user.profile
        profile.email_notifications = email_notifications
        profile.push_notifications = push_notifications
        profile.sms_notifications = sms_notifications
        profile.save()
        
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('notification_settings')
    
    context = {
        'profile': request.user.profile,
    }
    return render(request, 'notifications/settings.html', context)

@login_required
def get_unread_count(request):
    """Get unread notification count for AJAX requests"""
    unread_count = Notification.objects.filter(
        user=request.user.profile,
        read=False
    ).count()
    
    return JsonResponse({'unread_count': unread_count})

@login_required
def mark_notifications_read_batch(request):
    """Mark multiple notifications as read"""
    if request.method == 'POST':
        notification_ids = request.POST.getlist('notification_ids[]')
        
        if notification_ids:
            Notification.objects.filter(
                id__in=notification_ids,
                user=request.user.profile
            ).update(read=True)
            
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No notification IDs provided'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def create_notification(user, message):
    """Helper function to create notifications"""
    try:
        notification = Notification.objects.create(
            user=user,
            message=message
        )
        return notification
    except Exception as e:
        # Log error but don't break the main functionality
        print(f"Error creating notification: {e}")
        return None

def create_bulk_notifications(users, message):
    """Helper function to create notifications for multiple users"""
    notifications = []
    for user in users:
        notification = create_notification(user, message)
        if notification:
            notifications.append(notification)
    return notifications