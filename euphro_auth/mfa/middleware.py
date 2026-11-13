from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from .services import get_mfa_url, is_mfa_required, is_verified

ALLOWED_URL_NAMES = (
    "mfa_verify",
    "mfa_setup",
    "admin:logout",
    "cgu_acceptance",
    "static_cgu",
    "javascript-catalog",
)
ALLOWED_PATH_PREFIXES = ("/i18n/",)


def _is_allowed_path(path: str) -> bool:
    if path in {reverse(name) for name in ALLOWED_URL_NAMES}:
        return True
    # Media files are not served by this application (MEDIA_URL is unset).
    prefixes = [*ALLOWED_PATH_PREFIXES, settings.STATIC_URL]
    return any(
        prefix and prefix != "/" and path.startswith(prefix) for prefix in prefixes
    )


class AdminMFARequiredMiddleware:
    """Require a second factor for lab administrators' web sessions.

    Must run after django-otp's OTPMiddleware. It only looks at the session
    user: API clients authenticated by JWT have no session and are unaffected.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        if (
            is_mfa_required(user)
            and not is_verified(user)
            and not _is_allowed_path(request.path)
        ):
            if request.path.startswith("/api/"):
                return JsonResponse(
                    {
                        "detail": _("Multi-factor authentication is required."),
                        "code": "mfa_required",
                    },
                    status=403,
                )
            next_url = request.get_full_path() if request.method == "GET" else None
            return redirect(get_mfa_url(user, next_url))  # type: ignore[arg-type]
        return self.get_response(request)
