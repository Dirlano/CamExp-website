import re
from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:

	EXEMPT_URLS = [
		re.compile(r"^/$"),
		re.compile(r"^/accounts/login/?$"),
		re.compile(r"^/accounts/register/?$"),
		re.compile(r"^/accounts/logout/?$"),
		re.compile(r"^/admin/"),
		re.compile(r"^/static/"),
		re.compile(r"^/favicon\.ico$"),
		re.compile(r"^/\.well-known/"),
	]

	def __init__(self, get_response):

		self.get_response = get_response

	def __call__(self, request):

		path = request.path_info
		if not request.user.is_authenticated:
			for pattern in self.EXEMPT_URLS:
				if pattern.match(path):
					return self.get_response(request)
			# Redirect anonymous users to login page
			return redirect(f"{settings.LOGIN_URL}?next={path}")

		return self.get_response(request)


