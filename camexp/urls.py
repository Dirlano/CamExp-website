from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home, admin_initiate_call, video_call_room
from accounts.views import client_dashboard, expert_dashboard
from .admin import admin_site

# Custom error handlers
handler500 = 'camexp.views.custom_error_view'

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', home, name='home'),

    # Include accounts app URLs with namespace
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Other app URLs
    path('services/', include(('services.urls', 'services'), namespace='services')),
    path('payments/', include('payments.urls')),
    path('notifications/', include(('notifications.urls', 'notifications'), namespace='notifications')),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    path('chat/', include('chat.urls')),

    # API URLs
    path('api/services/', include('services.api.urls')),
    path('api/video-calls/', include('video_calls.api.urls')),

    # Dashboard URLs
    path('dashboard/client/', client_dashboard, name='client_dashboard'),
    path('dashboard/expert/', expert_dashboard, name='expert_dashboard'),
    path('dashboard/', client_dashboard, name='dashboard'),

    # Video Call URLs
    path('video-call/<str:room_identifier>/', video_call_room, name='video_call_room'),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)