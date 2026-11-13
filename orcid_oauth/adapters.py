from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.base import AuthError, AuthProcess
from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .completion import start_completion
from .invitations import (
    INVITATION_SESSION_KEY,
    clear_invitation,
    reject_invitation,
    validated_invitation_user,
)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """ORCID sign-in. An ORCID iD is linked to an account only through a
    validated invitation; it never creates an account."""

    def is_open_for_signup(self, request: HttpRequest, sociallogin) -> bool:
        return False

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        # Only sign-in is offered: no "connect" to the browser's current account.
        if sociallogin.state.get("process") != AuthProcess.LOGIN:
            raise ImmediateHttpResponse(reject_invitation(request))
        if INVITATION_SESSION_KEY in request.session:
            self._consume_invitation(request, sociallogin)
        if not sociallogin.is_existing:
            messages.warning(
                request,
                _(
                    # pylint: disable=line-too-long
                    "Your ORCID account isn't connected to an existing account. Please use email/password to sign in, or register with ORCID first using the link you received in the invitation email."
                ),
            )
            raise ImmediateHttpResponse(redirect("admin:login"))
        if not sociallogin.user.invitation_completed_at:
            raise ImmediateHttpResponse(start_completion(request, sociallogin))

    @staticmethod
    def _consume_invitation(request: HttpRequest, sociallogin: SocialLogin) -> None:
        # Keep invitation validation, association and consumption together so
        # concurrent callbacks cannot attach two identities to one invitation.
        with transaction.atomic():
            target = validated_invitation_user(
                request,
                for_callback=True,
                oauth_state=request.GET.get("state"),
                lock=True,
            )
            if target is None or (
                sociallogin.is_existing and sociallogin.user.pk != target.pk
            ):
                raise ImmediateHttpResponse(reject_invitation(request))
            if not sociallogin.is_existing:
                sociallogin.connect(request, target)
            clear_invitation(request)

    def on_authentication_error(
        self,
        request,
        provider,
        error=None,
        exception=None,
        extra_context=None,
    ):
        # Like the former Social Auth setup, return to the sign-in page.
        if error != AuthError.CANCELLED:
            messages.error(request, _("ORCID sign-in failed. Please try again."))
        raise ImmediateHttpResponse(redirect("admin:login"))
