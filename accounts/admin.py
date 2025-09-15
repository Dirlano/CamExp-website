from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0
    fields = ('user_type', 'bio', 'location')

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_user_type', 'get_location')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__user_type', 'profile__location')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__bio', 'profile__location')
    ordering = ('username',)
    
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

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'location', 'bio_preview')
    list_filter = ('user_type', 'location')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'bio', 'location')
    ordering = ('user__username',)
    readonly_fields = ('user',)
    
    def bio_preview(self, obj):
        return obj.bio[:100] + '...' if len(obj.bio) > 100 else obj.bio
    bio_preview.short_description = 'Bio Preview'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type')
        }),
        ('Profile Details', {
            'fields': ('bio', 'location')
        }),
    )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)