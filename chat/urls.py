from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Chat room
    path('room/<int:receiver_id>/', views.chat_room, name='chat_room'),
    
    # API endpoints
    path('api/send/<int:receiver_id>/', views.send_message, name='send_message'),
    path('api/messages/<int:receiver_id>/', views.get_messages, name='get_messages'),
    path('api/mark-read/<int:sender_id>/', views.mark_chat_read, name='mark_chat_read'),
    path('api/typing/<int:receiver_id>/', views.typing_indicator, name='typing_indicator'),
    path('api/search/', views.search_chats, name='search_chats'),
]