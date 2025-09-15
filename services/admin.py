from django.contrib import admin
from .models import ServiceListing, RequestPost, Reaction, Rating

class ServiceListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'expert', 'category', 'price', 'location', 'is_featured')
    list_filter = ('category', 'location', 'expert__user_type', 'is_featured')
    search_fields = ('title', 'description', 'expert__user__username', 'category', 'location')
    ordering = ('title',)
    
    fieldsets = (
        ('Service Information', {
            'fields': ('title', 'description', 'expert')
        }),
        ('Pricing & Location', {
            'fields': ('price', 'category', 'location')
        }),
        ('Additional Options', {
            'fields': ('is_featured',)
        }),
    )

class RequestPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'budget', 'status', 'accepted_expert')
    list_filter = ('status', 'budget', 'client__user_type')
    search_fields = ('title', 'description', 'client__user__username', 'accepted_expert__user__username')
    ordering = ('title',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('title', 'description', 'client')
        }),
        ('Budget & Status', {
            'fields': ('budget', 'status', 'accepted_expert')
        }),
    )

class ReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'get_content', 'get_content_type')
    list_filter = ('type', 'user__user_type')
    search_fields = ('user__user__username', 'type', 'post__title', 'request__title')
    ordering = ('id',)
    
    def get_content(self, obj):
        if obj.post:
            return obj.post.title
        elif obj.request:
            return obj.request.title
        return 'No Content'
    get_content.short_description = 'Content'
    
    def get_content_type(self, obj):
        if obj.post:
            return 'Service Listing'
        elif obj.request:
            return 'Request Post'
        return 'Unknown'
    get_content_type.short_description = 'Content Type'
    
    fieldsets = (
        ('Reaction Information', {
            'fields': ('user', 'type')
        }),
        ('Content', {
            'fields': ('post', 'request')
        }),
    )

class RatingAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'expert', 'score', 'review_preview')
    list_filter = ('score', 'reviewer__user_type', 'expert__user_type')
    search_fields = ('reviewer__user__username', 'expert__user__username', 'review')
    ordering = ('id',)
    
    def review_preview(self, obj):
        return obj.review[:100] + '...' if len(obj.review) > 100 else obj.review
    review_preview.short_description = 'Review Preview'
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('reviewer', 'expert', 'score')
        }),
        ('Review', {
            'fields': ('review',)
        }),
    )

admin.site.register(ServiceListing, ServiceListingAdmin)
admin.site.register(RequestPost, RequestPostAdmin)
admin.site.register(Reaction, ReactionAdmin)
admin.site.register(Rating, RatingAdmin)
