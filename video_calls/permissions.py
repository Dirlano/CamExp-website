from rest_framework import permissions

class CanCreateVideoCall(permissions.BasePermission):
    """
    Custom permission to only allow admins to create video calls.
    """

    def has_permission(self, request, view):
        # Allow if user is staff (Django admin) OR has the specific permission OR has user_type='admin'
        return (
            request.user.is_staff or
            request.user.has_perm('accounts.can_create_video_call') or
            request.user.user_type == 'admin'
        )