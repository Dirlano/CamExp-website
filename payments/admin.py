from django.contrib import admin
from .models import Payment

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'payer', 'payee', 'amount', 'status', 'provider', 'transaction_id', 'request_title')
    list_filter = ('status', 'provider', 'payer', 'payee')
    search_fields = ('payer__user__username', 'payee__user__username', 'transaction_id', 'request__title')
    ordering = ('id',)
    readonly_fields = ('payer', 'payee', 'request')
    
    def request_title(self, obj):
        return obj.request.title if obj.request else 'No Request'
    request_title.short_description = 'Request Title'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payer', 'payee', 'amount', 'status')
        }),
        ('Transaction Details', {
            'fields': ('provider', 'transaction_id', 'request')
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_pending']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} payment(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected payments as completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payment(s) marked as failed.')
    mark_as_failed.short_description = 'Mark selected payments as failed'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} payment(s) marked as pending.')
    mark_as_pending.short_description = 'Mark selected payments as pending'

admin.site.register(Payment, PaymentAdmin)
