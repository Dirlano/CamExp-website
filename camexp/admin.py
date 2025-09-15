from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

class CamexpAdminSite(AdminSite):
    site_header = "CamExp Administration"
    site_title = "CamExp Admin Portal"
    index_title = "Welcome to CamExp Administration"
    
    def index(self, request, extra_context=None):
        # Get statistics for the dashboard
        extra_context = extra_context or {}
        
        # User statistics
        from django.contrib.auth.models import User
        from accounts.models import Profile
        from services.models import ServiceListing, RequestPost, Payment
        from chat.models import Message
        from notifications.models import Notification
        from projects.models import Project
        
        total_users = User.objects.count()
        total_experts = Profile.objects.filter(user_type='expert').count()
        total_clients = Profile.objects.filter(user_type='client').count()
        
        # Service statistics
        total_services = ServiceListing.objects.count()
        total_requests = RequestPost.objects.count()
        open_requests = RequestPost.objects.filter(status='open').count()
        
        # Financial statistics
        total_payments = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Communication statistics
        total_messages = Message.objects.count()
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(read=False).count()
        
        # Project statistics
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='in_progress').count()
        completed_projects = Project.objects.filter(status='completed').count()
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_users = User.objects.filter(date_joined__gte=week_ago).count()
        recent_services = ServiceListing.objects.filter(
            created_at__gte=week_ago
        ).count() if hasattr(ServiceListing, 'created_at') else 0
        recent_payments = Payment.objects.filter(
            created_at__gte=week_ago
        ).count() if hasattr(Payment, 'created_at') else 0
        
        extra_context.update({
            'total_users': total_users,
            'total_experts': total_experts,
            'total_clients': total_clients,
            'total_services': total_services,
            'total_requests': total_requests,
            'open_requests': open_requests,
            'total_payments': total_payments,
            'total_messages': total_messages,
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'recent_users': recent_users,
            'recent_services': recent_services,
            'recent_payments': recent_payments,
        })
        
        return super().index(request, extra_context)

# Create custom admin site instance
admin_site = CamexpAdminSite(name='camexp_admin')

# Register all models with the custom admin site
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import Profile
from services.models import ServiceListing, RequestPost, Reaction, Rating
from chat.models import Message
from payments.models import Payment
from notifications.models import Notification
from projects.models import Project, Event

# User and Profile admin
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0
    fields = ('user_type', 'bio', 'location')

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_user_type', 'get_location', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__user_type', 'profile__location', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__bio', 'profile__location')
    ordering = ('-date_joined',)
    
    def get_user_type(self, obj):
        try:
            return obj.profile.user_type
        except Profile.DoesNotExist:
            return 'No Profile'
    get_user_type.short_description = 'User Type'
    
    def get_location(self, obj):
        try:
            return obj.profile.location
        except Profile.DoesNotExist:
            return 'No Location'
    get_location.short_description = 'Location'

# Register with custom admin site
admin_site.register(User, UserAdmin)
admin_site.register(Group)

# Import and register all the custom admin classes
from accounts.admin import ProfileAdmin
from services.admin import ServiceListingAdmin, RequestPostAdmin, ReactionAdmin, RatingAdmin
from chat.admin import MessageAdmin
from payments.admin import PaymentAdmin
from notifications.admin import NotificationAdmin
from projects.admin import ProjectAdmin, EventAdmin

admin_site.register(Profile, ProfileAdmin)
admin_site.register(ServiceListing, ServiceListingAdmin)
admin_site.register(RequestPost, RequestPostAdmin)
admin_site.register(Reaction, ReactionAdmin)
admin_site.register(Rating, RatingAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(Notification, NotificationAdmin)
admin_site.register(Project, ProjectAdmin)
admin_site.register(Event, EventAdmin)
