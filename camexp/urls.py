from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .views import home
from accounts.views import client_dashboard, expert_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('services/', include(('services.urls', 'services'), namespace='services')),
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    path('chat/', include('chat.urls')),
    
    # Dashboard URLs
    path('dashboard/client/', client_dashboard, name='client_dashboard'),
    path('dashboard/expert/', expert_dashboard, name='expert_dashboard'),
    path('dashboard/', client_dashboard, name='dashboard'),  # Default dashboard
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)