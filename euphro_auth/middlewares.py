from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from django.apps import apps
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from lab.participations.gate import get_required_employer_completion_url
from orcid_oauth.views import is_completion_required

from .mfa import services as mfa_services
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


# Reachable whatever the gates.
ALWAYS_ALLOWED = {
    "admin:logout",
    "account_logout",
    "static_cgu",
    "javascript-catalog",
    "set_language",
}
MFA_ALLOWED = {"mfa_activate_totp", "mfa_reauthenticate", "cgu_acceptance"}


@dataclass
class Gate:
    code: str
    detail: str
    redirect_url: str

    def response(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "detail": self.detail,
                    "code": self.code,
                    "redirect_url": self.redirect_url,
                },
                status=403,
            )
        return redirect(self.redirect_url)


class AccountGatesMiddleware:
    """Steps a signed-in session must complete, in this order:

    1. second factor, for administrators (euphro_auth.mfa);
    2. account information, for invited users who signed in with ORCID;
    3. acceptance of the latest CGU;
    4. employer information, for the projects that require it.

    Pages are redirected to the step; API calls get a JSON 403 with
    ``detail``, ``code`` and ``redirect_url``. Only the session user is
    checked: API clients authenticated by JWT carry their MFA state in the
    token (see euphro_auth.jwt)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.employer_gate_enabled = apps.is_installed("radiation_protection")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(
        self, request: HttpRequest, view_func, view_args, view_kwargs
    ):  # pylint: disable=unused-argument
        user = request.user
        match = request.resolver_match
        view_name = match.view_name if match else None
        if not user.is_authenticated or view_name in ALWAYS_ALLOWED:
            return None
        if mfa_services.is_mfa_required(user) and not (
            mfa_services.is_session_verified(request, user)
        ):
            # Until verified, only the MFA pages and the CGU page are reachable.
            if view_name in MFA_ALLOWED:
                return None
            return self._mfa_gate(request).response(request)
        gate = (
            self._completion_gate(request, view_name)
            or self._cgu_gate(request, view_name)
            or self._employer_gate(request, view_kwargs)
        )
        return gate.response(request) if gate else None

    @staticmethod
    def _mfa_gate(request: HttpRequest) -> Gate:
        user = cast(User, request.user)
        next_url = request.get_full_path() if request.method == "GET" else None
        return Gate(
            code="mfa_required",
            detail=_("Multi-factor authentication is required."),
            redirect_url=mfa_services.get_mfa_url(user, next_url),
        )

    @staticmethod
    def _completion_gate(request: HttpRequest, view_name: str | None) -> Gate | None:
        user = cast(User, request.user)
        if view_name == "complete_registration_orcid" or not is_completion_required(
            user
        ):
            return None
        return Gate(
            code="account_completion_required",
            detail=_("You must complete your account information to continue."),
            redirect_url=reverse("complete_registration_orcid"),
        )

    @staticmethod
    def _cgu_gate(request: HttpRequest, view_name: str | None) -> Gate | None:
        user = cast(User, request.user)
        if view_name == "cgu_acceptance" or _check_cgu_acceptance(user):
            return None
        return Gate(
            code="cgu_acceptance_required",
            detail=_("You must accept the Terms and Conditions to continue."),
            redirect_url=reverse("cgu_acceptance"),
        )

    def _employer_gate(self, request: HttpRequest, view_kwargs) -> Gate | None:
        if not self.employer_gate_enabled:
            return None
        url = get_required_employer_completion_url(request, view_kwargs)
        if url is None:
            return None
        return Gate(
            code="employer_information_required",
            detail=_("Employer information is required for this project."),
            redirect_url=url,
        )
