from django import template

register = template.Library()

@register.filter
def filter_type(queryset, notification_type):
    """Filter notifications by type"""
    return queryset.filter(notification_type=notification_type) if queryset else []
