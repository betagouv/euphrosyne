"""Count password failures by lowercased email on the web login form.

Axes manages expiry with its standard cool-off. ORCID, existing sessions and
JWT refresh remain available. Password successes reset failures in
LowercaseEmailBackend; passwordless logins leave them intact.
"""

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _


def account_username(
    request: HttpRequest, credentials: dict | None = None
) -> str | None:
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
