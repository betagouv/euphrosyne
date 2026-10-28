"""Share password failures by lowercased email across web, Basic and JWT.

Axes manages expiry with its standard cool-off. ORCID, existing sessions and
JWT refresh remain available. Password successes reset failures in
LowercaseEmailBackend; passwordless logins leave them intact.
"""

from axes.handlers.database import AxesDatabaseHandler
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from rest_framework.request import Request


def account_username(
    request: HttpRequest, credentials: dict | None = None
) -> str | None:
    """Use the same email for HTML username, Basic username and JWT email."""
    data = credentials if credentials is not None else request.POST
    username = data.get("email") or data.get("username")
    return username.lower() if isinstance(username, str) else None


def is_passwordless_authentication(
    request: HttpRequest, credentials: dict | None = None
) -> bool:
    # Credentials come from Django's authenticate(), never client-supplied flags.
    # Django masks passwords in failure signals, but preserves the key.
    # pylint: disable=unused-argument
    return credentials is not None and credentials.get("password") is None


class AccountAxesHandler(AxesDatabaseHandler):
    def user_login_failed(self, sender, credentials: dict, request=None, **kwargs):
        super().user_login_failed(sender, credentials, request=request, **kwargs)
        if isinstance(request, Request):
            # DRF stores attributes on its wrapper. AxesMiddleware receives the
            # underlying Django request, so expose the lockout there as well.
            # pylint: disable=protected-access
            request._request.axes_locked_out = request.axes_locked_out
            request._request.axes_credentials = credentials


def password_lockout_response(
    request: HttpRequest,
    original_response: HttpResponse | None = None,
    credentials: dict | None = None,
) -> HttpResponse:
    # pylint: disable=unused-argument
    message = _(
        "Password sign-in is blocked for 15 minutes after too many failed attempts. "
        "You can still log in with ORCID."
    )
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": message}, status=429)
    return render(
        request,
        "euphro_admin/login.html",
        {
            **admin.site.each_context(request),
            "title": _("Log in"),
            "password_lockout_message": message,
        },
        status=429,
    )
