import logging

from allauth.account.decorators import reauthentication_required
from allauth.mfa.base import views as base_views
from allauth.mfa.totp import views as totp_views
from allauth.mfa.totp.internal import flows as totp_flows
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from lab.permissions import is_lab_admin

from . import services

logger = logging.getLogger(__name__)


def _check_mfa_user(request: HttpRequest) -> None:
    # MFA is offered to administrators only for now, who cannot be
    # impersonated. Anonymous requests are left to allauth, which redirects them
    # to the sign-in page.
    if not request.user.is_authenticated:
        return
    if not is_lab_admin(request.user):
        raise PermissionDenied


class IndexView(base_views.IndexView):
    """Account security page."""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        _check_mfa_user(request)
        return super().dispatch(request, *args, **kwargs)


class ReauthenticateView(base_views.ReauthenticateView):
    """Fresh code asked before removing a factor (see DeactivateTOTPView)."""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        _check_mfa_user(request)
        return super().dispatch(request, *args, **kwargs)


class ActivateTOTPView(totp_views.ActivateTOTPView):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        _check_mfa_user(request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        totp_flows.activate_totp(self.request, form)
        logger.info("MFA TOTP enrolled for user %s", self.request.user.pk)
        # A signed-in session is never verified: the next sign-in asks for a
        # code (AuthenticateStage), and Django's login() renews the session key
        # and the CSRF token. allauth's message (mfa/messages/totp_activated.txt)
        # asks the user to sign in again.
        logout(self.request)
        return redirect("account_login")


class DeactivateTOTPView(totp_views.DeactivateTOTPView):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        _check_mfa_user(request)
        return super().dispatch(request, *args, **kwargs)

    # Removing the factor needs a fresh code or password, even within a verified
    # session. Enrollment does not (MFA_REAUTHENTICATION_REQUIRED is off): it
    # follows sign-in, and ORCID accounts have no password to give.
    @method_decorator(reauthentication_required)
    def _dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        return super()._dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        totp_flows.deactivate_totp(self.request, self.authenticator)
        services.end_sessions(self.request.user, keep=self.request.session.session_key)
        services.forget_verification(self.request)
        logger.warning("MFA TOTP removed by user %s", self.request.user.pk)
        # An administrator sets up a new factor straight away.
        if services.is_mfa_required(self.request.user):
            return redirect("mfa_activate_totp")
        return redirect("mfa_index")
