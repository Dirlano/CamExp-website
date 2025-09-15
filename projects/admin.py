from django.contrib import admin
from .models import Project, Event

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_title', 'status', 'get_client', 'get_expert')
    list_filter = ('status',)
    search_fields = ('request__title', 'request__client__user__username', 'request__accepted_expert__user__username')
    ordering = ('id',)
    readonly_fields = ('request',)
    
    def request_title(self, obj):
        return obj.request.title
    request_title.short_description = 'Request Title'
    
    def get_client(self, obj):
        return obj.request.client.user.username
    get_client.short_description = 'Client'
    
    def get_expert(self, obj):
        return obj.request.accepted_expert.user.username if obj.request.accepted_expert else 'Not Assigned'
    get_expert.short_description = 'Expert'
    
    fieldsets = (
        ('Project Information', {
            'fields': ('request', 'status')
        }),
    )
    
    actions = ['mark_as_pending', 'mark_as_in_progress', 'mark_as_completed']
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} project(s) marked as pending.')
    mark_as_pending.short_description = 'Mark selected projects as pending'
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} project(s) marked as in progress.')
    mark_as_in_progress.short_description = 'Mark selected projects as in progress'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} project(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected projects as completed'

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'start', 'end', 'duration')
    list_filter = ('project__status', 'start', 'end')
    search_fields = ('title', 'project__request__title')
    ordering = ('start',)
    
    def duration(self, obj):
        from django.utils import timezone
        if obj.start and obj.end:
            duration = obj.end - obj.start
            hours = duration.total_seconds() / 3600
            return f"{hours:.1f} hours"
        return "N/A"
    duration.short_description = 'Duration'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'project')
        }),
        ('Schedule', {
            'fields': ('start', 'end')
        }),
    )

admin.site.register(Project, ProjectAdmin)
admin.site.register(Event, EventAdmin)
