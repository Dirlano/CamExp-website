from django.urls import path
from .views import (
    list_notifications,
    mark_as_read,
    mark_all_as_read,
    delete_notification,
    clear_all_notifications,
    notification_settings,
    get_unread_count,
    mark_notifications_read_batch,
)

urlpatterns = [
    path('', list_notifications, name='list'),
    path('settings/', notification_settings, name='settings'),
    
    # API endpoints
    path('api/mark_read/<int:notification_id>/', mark_as_read, name='mark_as_read'),
    path('api/mark_all_read/', mark_all_as_read, name='mark_all_read'),
    path('api/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
    path('api/clear_all/', clear_all_notifications, name='clear_all'),
    path('api/unread_count/', get_unread_count, name='unread_count'),
    path('api/mark_read_batch/', mark_notifications_read_batch, name='mark_read_batch'),
]

# Add app_name for URL namespacing
app_name = 'notifications'