from django.urls import path
from .views import (
    chat_room,
    chat_list,
    send_message,
    get_messages,
    delete_message,
    mark_chat_read,
    search_chats,
    typing_indicator,
)

urlpatterns = [
    path('', chat_list, name='chat_list'),
    path('<int:receiver_id>/', chat_room, name='chat_room'),
    
    # API endpoints
    path('api/send/<int:receiver_id>/', send_message, name='send_message'),
    path('api/messages/<int:receiver_id>/', get_messages, name='get_messages'),
    path('api/delete/<int:message_id>/', delete_message, name='delete_message'),
    path('api/mark_read/<int:sender_id>/', mark_chat_read, name='mark_chat_read'),
    path('api/search/', search_chats, name='search_chats'),
    path('api/typing/<int:receiver_id>/', typing_indicator, name='typing_indicator'),
]