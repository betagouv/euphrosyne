from collections.abc import Callable

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from .models import User
from .sessions import get_session_idle_timeout


class SessionIdleTimeoutMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Before the view, request.user comes from Django's session authentication,
        # not from DRF's JWT authentication. set_expiry also marks the session dirty.
        if request.user.is_authenticated:
            request.session.set_expiry(get_session_idle_timeout(request.user))
        response = self.get_response(request)
        # Social Auth resets expiry after emitting user_logged_in. Reapply the
        # policy only when the view's user belongs to the authenticated session:
        # DRF may have replaced request.user with a user authenticated by JWT.
        if request.user.is_authenticated and request.session.get(SESSION_KEY) == str(
            request.user.pk
        ):
            request.session.set_expiry(get_session_idle_timeout(request.user))
        return response


def _check_cgu_acceptance(user: User) -> bool:
    if not settings.FORCE_LAST_CGU_ACCEPTANCE_DT:
        return True
    if (
        user.cgu_accepted_at
        and user.cgu_accepted_at >= settings.FORCE_LAST_CGU_ACCEPTANCE_DT
    ):
        return True
    return False


class CGUAcceptanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not _check_cgu_acceptance(request.user):
            if request.path not in [
                reverse("cgu_acceptance"),
                reverse("admin:logout"),
                reverse("static_cgu"),
            ]:
                return redirect("cgu_acceptance")
        response = self.get_response(request)
        return response
