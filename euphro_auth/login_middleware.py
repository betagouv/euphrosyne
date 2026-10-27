import math
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.cache import patch_cache_control
from django.utils.translation import gettext as _


class LoginLockoutMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        locked_until = getattr(request, "login_locked_until", None)
        if locked_until is None:
            return response

        message = _("Too many login attempts. Please try again later.")
        if request.path_info.startswith("/api/"):
            response = JsonResponse({"detail": message}, status=429)
        else:
            response = render(
                request,
                "euphro_auth/login_locked.html",
                {"title": _("Too many login attempts"), "lockout_message": message},
                status=429,
            )
        response["Retry-After"] = str(
            max(1, math.ceil((locked_until - timezone.now()).total_seconds()))
        )
        patch_cache_control(response, no_store=True)
        return response
