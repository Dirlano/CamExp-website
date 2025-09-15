from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import Message
from accounts.models import Profile

@login_required
def chat_room(request, receiver_id):
    """Enhanced chat room with message history and real-time features"""
    receiver = get_object_or_404(Profile, id=receiver_id)
    
    # Check if user is not trying to chat with themselves
    if request.user.profile == receiver:
        messages.error(request, 'You cannot chat with yourself.')
        return redirect('dashboard')
    
    # Room name as min(sender_id, receiver_id)_max
    room_name = f'{min(request.user.id, receiver_id)}_{max(request.user.id, receiver_id)}'
    
    # Get chat history
    messages_list = Message.objects.filter(
        Q(sender=request.user.profile, receiver=receiver) |
        Q(sender=receiver, receiver=request.user.profile)
    ).order_by('timestamp')
    
    # Mark messages as read
    unread_messages = messages_list.filter(
        receiver=request.user.profile,
        is_read=False
    )
    unread_messages.update(is_read=True)
    
    # Get user's recent chats
    recent_chats = get_recent_chats(request.user.profile)
    
    # Get online status (placeholder for future WebSocket implementation)
    receiver_online = False  # This would be updated via WebSocket
    
    context = {
        'room_name': room_name,
        'receiver': receiver,
        'messages': messages_list,
        'recent_chats': recent_chats,
        'receiver_online': receiver_online,
    }
    return render(request, 'chat/room.html', context)

@login_required
def chat_list(request):
    """List of all user's chats"""
    # Get all users the current user has chatted with
    chat_partners = Profile.objects.filter(
        Q(message_sent__receiver=request.user.profile) |
        Q(message_received__sender=request.user.profile)
    ).distinct().exclude(id=request.user.profile.id)
    
    # Get last message for each chat partner
    chat_list_data = []
    for partner in chat_partners:
        last_message = Message.objects.filter(
            Q(sender=request.user.profile, receiver=partner) |
            Q(sender=partner, receiver=request.user.profile)
        ).order_by('-timestamp').first()
        
        unread_count = Message.objects.filter(
            sender=partner,
            receiver=request.user.profile,
            is_read=False
        ).count()
        
        chat_list_data.append({
            'partner': partner,
            'last_message': last_message,
            'unread_count': unread_count,
            'last_activity': last_message.timestamp if last_message else None
        })
    
    # Sort by last activity
    chat_list_data.sort(key=lambda x: x['last_activity'] or timezone.now(), reverse=True)
    
    context = {
        'chat_list': chat_list_data,
    }
    return render(request, 'chat/list.html', context)

@login_required
def send_message(request, receiver_id):
    """Send a message via AJAX"""
    if request.method == 'POST':
        receiver = get_object_or_404(Profile, id=receiver_id)
        message_text = request.POST.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'})
        
        # Create the message
        message = Message.objects.create(
            sender=request.user.profile,
            receiver=receiver,
            content=message_text
        )
        
        # Create notification for receiver
        from notifications.views import create_notification
        create_notification(
            user=receiver,
            message=f'New message from {request.user.get_full_name()}',
            notification_type='new_message',
            related_object=message
        )
        
        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'sender_name': request.user.get_full_name()
        })
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def get_messages(request, receiver_id):
    """Get messages for a specific chat via AJAX"""
    receiver = get_object_or_404(Profile, id=receiver_id)
    
    # Get messages since last request
    last_message_id = request.GET.get('last_message_id', 0)
    
    messages_list = Message.objects.filter(
        Q(sender=request.user.profile, receiver=receiver) |
        Q(sender=receiver, receiver=request.user.profile)
    ).filter(id__gt=last_message_id).order_by('timestamp')
    
    # Mark messages as read
    unread_messages = messages_list.filter(
        receiver=request.user.profile,
        is_read=False
    )
    unread_messages.update(is_read=True)
    
    # Format messages for JSON response
    formatted_messages = []
    for msg in messages_list:
        formatted_messages.append({
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.user.get_full_name(),
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'is_own': msg.sender == request.user.profile
        })
    
    return JsonResponse({
        'status': 'success',
        'messages': formatted_messages,
        'has_new': len(formatted_messages) > 0
    })

@login_required
def delete_message(request, message_id):
    """Delete a message (only sender can delete)"""
    if request.method == 'POST':
        try:
            message = Message.objects.get(
                id=message_id,
                sender=request.user.profile
            )
            message.delete()
            return JsonResponse({'status': 'success'})
        except Message.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def mark_chat_read(request, sender_id):
    """Mark all messages from a sender as read"""
    if request.method == 'POST':
        sender = get_object_or_404(Profile, id=sender_id)
        
        Message.objects.filter(
            sender=sender,
            receiver=request.user.profile,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def search_chats(request):
    """Search through chat messages"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'status': 'error', 'message': 'Search query required'})
    
    # Search in message content
    matching_messages = Message.objects.filter(
        Q(content__icontains=query) &
        (Q(sender=request.user.profile) | Q(receiver=request.user.profile))
    ).order_by('-timestamp')
    
    # Get unique chat partners from search results
    chat_partners = set()
    for msg in matching_messages:
        if msg.sender == request.user.profile:
            chat_partners.add(msg.receiver)
        else:
            chat_partners.add(msg.sender)
    
    # Format results
    search_results = []
    for partner in chat_partners:
        # Get the matching message for this partner
        matching_msg = matching_messages.filter(
            Q(sender=partner) | Q(receiver=partner)
        ).first()
        
        search_results.append({
            'partner': partner,
            'matching_message': matching_msg,
            'relevance_score': 1  # You could implement relevance scoring here
        })
    
    # Sort by relevance and timestamp
    search_results.sort(key=lambda x: x['matching_message'].timestamp, reverse=True)
    
    return JsonResponse({
        'status': 'success',
        'results': search_results[:20]  # Limit results
    })

def get_recent_chats(profile):
    """Get user's recent chat conversations"""
    # Get all chat partners
    chat_partners = Profile.objects.filter(
        Q(message_sent__receiver=profile) |
        Q(message_received__sender=profile)
    ).distinct().exclude(id=profile.id)
    
    recent_chats = []
    for partner in chat_partners:
        last_message = Message.objects.filter(
            Q(sender=profile, receiver=partner) |
            Q(sender=partner, receiver=profile)
        ).order_by('-timestamp').first()
        
        unread_count = Message.objects.filter(
            sender=partner,
            receiver=profile,
            is_read=False
        ).count()
        
        recent_chats.append({
            'partner': partner,
            'last_message': last_message,
            'unread_count': unread_count,
            'last_activity': last_message.timestamp if last_message else None
        })
    
    # Sort by last activity and limit to 10
    recent_chats.sort(key=lambda x: x['last_activity'] or timezone.now(), reverse=True)
    return recent_chats[:10]

@login_required
def typing_indicator(request, receiver_id):
    """Handle typing indicators (placeholder for WebSocket implementation)"""
    if request.method == 'POST':
        is_typing = request.POST.get('is_typing') == 'true'
        
        # In a real implementation, you would broadcast this via WebSocket
        # For now, we'll just return success
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)