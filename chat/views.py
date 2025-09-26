from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max, Case, When, Value, IntegerField
from django.utils import timezone
from django.views.decorators.http import require_http_methods
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
    room_name = f'{min(request.user.id, receiver.user.id)}_{max(request.user.id, receiver.user.id)}'
    
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
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    # Get user's recent chats
    recent_chats = get_recent_chats(request.user.profile)
    
    context = {
        'room_name': room_name,
        'receiver': receiver,
        'messages': messages_list,
        'recent_chats': recent_chats,
    }
    return render(request, 'chat/room.html', context)

@login_required
@require_http_methods(["POST"])
def send_message(request, receiver_id):
    """Send a message via AJAX"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    receiver = get_object_or_404(Profile, id=receiver_id)
    content = request.POST.get('message', '').strip()
    
    if not content:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    
    # Create and save message
    message = Message.objects.create(
        sender=request.user.profile,
        receiver=receiver,
        content=content
    )
    
    return JsonResponse({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'is_read': message.is_read
        }
    })

@login_required
def get_messages(request, receiver_id):
    """Get messages for a specific chat via AJAX"""
    receiver = get_object_or_404(Profile, id=receiver_id)
    last_message_id = request.GET.get('last_message_id', 0)
    
    messages_list = Message.objects.filter(
        Q(sender=request.user.profile, receiver=receiver) |
        Q(sender=receiver, receiver=request.user.profile)
    )
    
    if last_message_id:
        messages_list = messages_list.filter(id__gt=last_message_id)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'is_read': msg.is_read,
        'is_sender': msg.sender == request.user.profile,
        'sender_name': msg.sender.user.get_full_name() or msg.sender.user.username,
        'sender_avatar': msg.sender.avatar.url if msg.sender.avatar else ''
    } for msg in messages_list.order_by('timestamp')]
    
    # Mark messages as read
    if messages_list.exists():
        unread_messages = messages_list.filter(
            receiver=request.user.profile,
            is_read=False
        )
        unread_messages.update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({'messages': messages_data})

@login_required
def get_recent_chats(profile):
    """Get user's recent chat conversations"""
    # Get the most recent message for each conversation
    sent_messages = Message.objects.filter(
        sender=profile
    ).values('receiver').annotate(
        last_message=Max('timestamp'),
        unread_count=Count('id', filter=Q(is_read=False))
    )
    
    received_messages = Message.objects.filter(
        receiver=profile
    ).values('sender').annotate(
        last_message=Max('timestamp'),
        unread_count=Count('id', filter=Q(is_read=False))
    )
    
    # Combine and process the results
    all_chats = {}
    
    for msg in sent_messages:
        user_id = msg['receiver']
        if user_id not in all_chats or msg['last_message'] > all_chats[user_id]['last_message']:
            all_chats[user_id] = {
                'last_message': msg['last_message'],
                'unread_count': msg['unread_count']
            }
    
    for msg in received_messages:
        user_id = msg['sender']
        if user_id not in all_chats or msg['last_message'] > all_chats[user_id]['last_message']:
            all_chats[user_id] = {
                'last_message': msg['last_message'],
                'unread_count': msg['unread_count']
            }
    
    # Get the actual profile objects and last messages
    recent_chats = []
    for user_id, data in sorted(all_chats.items(), key=lambda x: x[1]['last_message'], reverse=True):
        try:
            user_profile = Profile.objects.get(id=user_id)
            last_message = Message.objects.filter(
                Q(sender=profile, receiver=user_profile) |
                Q(sender=user_profile, receiver=profile)
            ).order_by('-timestamp').first()
            
            recent_chats.append({
                'user': user_profile,
                'last_message': last_message,
                'unread_count': data['unread_count']
            })
        except Profile.DoesNotExist:
            continue
    
    return recent_chats

@login_required
def mark_chat_read(request, sender_id):
    """Mark all messages from a sender as read"""
    sender = get_object_or_404(Profile, id=sender_id)
    updated = Message.objects.filter(
        sender=sender,
        receiver=request.user.profile,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({'status': 'success', 'updated': updated})

@login_required
def search_chats(request):
    """Search through chat messages"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'messages': []})
    
    # Search in messages where user is either sender or receiver
    messages = Message.objects.filter(
        Q(content__icontains=query) &
        (Q(sender=request.user.profile) | Q(receiver=request.user.profile))
    ).select_related('sender__user', 'receiver__user').order_by('-timestamp')
    
    results = []
    for msg in messages:
        other_user = msg.receiver if msg.sender == request.user.profile else msg.sender
        results.append({
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'other_user': {
                'id': other_user.id,
                'name': other_user.user.get_full_name() or other_user.user.username,
                'avatar': other_user.avatar.url if other_user.avatar else ''
            },
            'is_sender': msg.sender == request.user.profile
        })
    
    return JsonResponse({'messages': results})

@login_required
def typing_indicator(request, receiver_id):
    """Handle typing indicators"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        is_typing = request.POST.get('is_typing', 'false') == 'true'
        # This is a placeholder - actual implementation would use WebSockets
        return JsonResponse({'status': 'success', 'is_typing': is_typing})
    return JsonResponse({'error': 'Invalid request'}, status=400)