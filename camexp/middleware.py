import re
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:

    EXEMPT_URLS = [
        re.compile(r"^/$"),
        re.compile(r"^/login/?$"),
        re.compile(r"^/accounts/register/?$"),
        re.compile(r"^/accounts/logout/?$"),
        re.compile(r"^/admin/"),
        re.compile(r"^/static/"),
        re.compile(r"^/media/"),
        re.compile(r"^/favicon\.ico$"),
        re.compile(r"^/\.well-known/"),
        re.compile(r"^/dashboard/.*$"),
        re.compile(r"^/accounts/password_reset/.*$"),
        re.compile(r"^/accounts/reset/.*$"),
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # Check if the path is in the exempt list
        if any(pattern.match(path) for pattern in self.EXEMPT_URLS):
            return self.get_response(request)
            
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Prevent redirect loops by checking if we're already going to login
            if path.startswith('/accounts/login/'):
                return self.get_response(request)
                
            login_url = reverse('login')
            # Remove any existing 'next' parameter to prevent loops
            next_url = path if path != login_url else '/'
            return redirect(f"{login_url}?next={next_url}")

        return self.get_response(request)
