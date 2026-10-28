"""Application adapters for Axes; attempt tracking and expiry belong to Axes."""

import math

from axes.models import AccessAttempt
from axes.signals import user_locked_out
from django.conf import settings
from django.db.models import Max
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.cache import patch_cache_control
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext as _


def get_username(request, credentials=None):
    data = credentials or getattr(request, "data", getattr(request, "POST", {}))
    username = data.get("username") or data.get("email")
    if not isinstance(username, str) or not username.strip():
        return None
    return salted_hmac(
        "euphro_auth.axes", username.lower(), algorithm="sha256"
    ).hexdigest()


def get_client_ip(_request):
    # A fixed redacted value preserves Axes' unique constraint during parallel
    # first attempts; SQL NULL would allow duplicate rows for the same client.
    return "0.0.0.0"


def bypass_non_password_auth(request, _credentials):
    return not getattr(request, "axes_password_attempt", False)


@receiver(user_locked_out, dispatch_uid="euphro_auth.axes.lockout")
def propagate_api_lockout(request, **_kwargs):
    """Make a DRF Request's lockout visible to the stock Axes middleware."""
    raw_request = getattr(request, "_request", request)
    raw_request.axes_locked_out = True
    raw_request.axes_credentials = getattr(request, "axes_credentials", None)


def lockout_response(request, _response=None, credentials=None):
    credentials = credentials or getattr(request, "axes_credentials", None)
    last_attempt = AccessAttempt.objects.filter(
        username=get_username(request, credentials)
    ).aggregate(last=Max("attempt_time"))["last"]
    retry_after = 1
    if last_attempt is not None:
        expires_at = last_attempt + settings.AXES_COOLOFF_TIME
        retry_after = max(1, math.ceil((expires_at - timezone.now()).total_seconds()))

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
    response["Retry-After"] = str(retry_after)
    patch_cache_control(response, no_store=True)
    return response
