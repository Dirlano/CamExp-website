from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home
from accounts.views import client_dashboard, expert_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    
    # Include accounts app URLs with namespace
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    
    # Other app URLs
    path('services/', include(('services.urls', 'services'), namespace='services')),
    path('payments/', include('payments.urls')),
    path('notifications/', include(('notifications.urls', 'notifications'), namespace='notifications')),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    path('chat/', include('chat.urls')),
    
    # Dashboard URLs
    path('dashboard/client/', client_dashboard, name='client_dashboard'),
    path('dashboard/expert/', expert_dashboard, name='expert_dashboard'),
    path('dashboard/', client_dashboard, name='dashboard'),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)