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
    path('', list_notifications, name='notifications'),
    path('settings/', notification_settings, name='notification_settings'),
    
    # API endpoints
    path('api/mark_read/<int:notification_id>/', mark_as_read, name='mark_as_read'),
    path('api/mark_all_read/', mark_all_as_read, name='mark_all_as_read'),
    path('api/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
    path('api/clear_all/', clear_all_notifications, name='clear_all_notifications'),
    path('api/unread_count/', get_unread_count, name='get_unread_count'),
    path('api/mark_batch_read/', mark_notifications_read_batch, name='mark_batch_read'),
]