import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, Profile
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Add user to their personal group for notifications
        if self.user.is_authenticated:
            await self.channel_layer.group_add(
                f'user_{self.user.id}',
                self.channel_name
            )
            # Update user's online status
            await self.set_user_online(True)
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Remove from personal group
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f'user_{self.user.id}',
                self.channel_name
            )
            # Update user's online status
            await self.set_user_online(False)
    
    @database_sync_to_async
    def set_user_online(self, is_online):
        """Update user's online status"""
        if self.user.is_authenticated:
            try:
                profile = Profile.objects.get(user=self.user)
                profile.is_online = is_online
                if not is_online:
                    profile.last_seen = timezone.now()
                profile.save(update_fields=['is_online', 'last_seen'])
                return True
            except Profile.DoesNotExist:
                return False
        return False
    
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        """Save message to database"""
        try:
            sender = Profile.objects.get(user_id=sender_id)
            receiver = Profile.objects.get(id=receiver_id)
            message = Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=content
            )
            return {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'sender_id': sender.id,
                'receiver_id': receiver.id,
                'is_read': message.is_read
            }
        except (Profile.DoesNotExist, Exception) as e:
            print(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def get_user_profile(self, user_id):
        """Get user profile data"""
        try:
            profile = Profile.objects.get(user_id=user_id)
            return {
                'id': profile.id,
                'username': profile.user.username,
                'full_name': profile.user.get_full_name(),
                'avatar': profile.avatar.url if profile.avatar else None,
                'is_online': profile.is_online
            }
        except Profile.DoesNotExist:
            return None

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing_indicator(text_data_json)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(text_data_json)
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message"""
        message = data['message']
        receiver_id = data.get('receiver_id')
        
        if not message or not receiver_id or not self.user.is_authenticated:
            return
        
        # Save message to database
        message_data = await self.save_message(
            self.user.id,
            receiver_id,
            message
        )
        
        if message_data:
            # Get sender profile
            sender_profile = await self.get_user_profile(self.user.id)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data['content'],
                    'sender_id': sender_profile['id'],
                    'sender_username': sender_profile['username'],
                    'sender_avatar': sender_profile['avatar'],
                    'timestamp': message_data['timestamp'],
                    'message_id': message_data['id']
                }
            )
            
            # Send notification to receiver if they're not in the chat
            await self.channel_layer.group_send(
                f'user_{receiver_id}',
                {
                    'type': 'chat_notification',
                    'sender_id': sender_profile['id'],
                    'sender_username': sender_profile['username'],
                    'message': message_data['content'],
                    'room_name': self.room_name
                }
            )
    
    async def handle_typing_indicator(self, data):
        """Handle typing indicators"""
        is_typing = data.get('is_typing', False)
        receiver_id = data.get('receiver_id')
        
        if not receiver_id or not self.user.is_authenticated:
            return
        
        # Get user profile
        user_profile = await self.get_user_profile(self.user.id)
        
        # Send typing indicator to the other user
        await self.channel_layer.group_send(
            f'user_{receiver_id}',
            {
                'type': 'typing_indicator',
                'user_id': user_profile['id'],
                'username': user_profile['username'],
                'is_typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle read receipts"""
        message_id = data.get('message_id')
        
        if not message_id or not self.user.is_authenticated:
            return
        
        # Mark message as read
        await self.mark_message_as_read(message_id)
        
        # Notify sender that their message was read
        message_info = await self.get_message_info(message_id)
        if message_info and message_info['sender_id'] != self.user.id:
            await self.channel_layer.group_send(
                f'user_{message_info['sender_id']}',
                {
                    'type': 'message_read',
                    'message_id': message_id,
                    'read_by': self.user.id,
                    'read_at': timezone.now().isoformat()
                }
            )
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark a message as read"""
        try:
            message = Message.objects.get(id=message_id, receiver__user=self.user)
            if not message.is_read:
                message.is_read = True
                message.read_at = timezone.now()
                message.save(update_fields=['is_read', 'read_at'])
                return True
        except Message.DoesNotExist:
            return False
        return False
    
    @database_sync_to_async
    def get_message_info(self, message_id):
        """Get basic info about a message"""
        try:
            message = Message.objects.get(id=message_id)
            return {
                'id': message.id,
                'sender_id': message.sender.user.id,
                'receiver_id': message.receiver.id,
                'content': message.content,
                'is_read': message.is_read,
                'timestamp': message.timestamp.isoformat()
            }
        except Message.DoesNotExist:
            return None

    # Receive message from room group
    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'sender_avatar': event.get('sender_avatar'),
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))
    
    async def chat_notification(self, event):
        """Send chat notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'message': event['message'],
            'room_name': event['room_name']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def message_read(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'read_by': event['read_by'],
            'read_at': event['read_at']
        }))