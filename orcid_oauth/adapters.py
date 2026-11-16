from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.base import AuthProcess
from django.db import transaction
from django.http import HttpRequest

from .invitations import (
    INVITATION_SESSION_KEY,
    clear_invitation,
    reject_invitation,
    validated_invitation_user,
)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """ORCID sign-in. An ORCID iD is linked to an account only through a
    validated invitation; it never creates an account (allauth then shows
    account/signup_closed.html)."""

    def is_open_for_signup(self, request: HttpRequest, sociallogin) -> bool:
        return False

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        # Only sign-in is offered: no "connect" to the browser's current account.
        if sociallogin.state.get("process") != AuthProcess.LOGIN:
            raise ImmediateHttpResponse(reject_invitation(request))
        if INVITATION_SESSION_KEY in request.session:
            self._consume_invitation(request, sociallogin)

    @staticmethod
    def _consume_invitation(request: HttpRequest, sociallogin: SocialLogin) -> None:
        # Keep invitation validation, association and consumption together so
        # concurrent callbacks cannot attach two identities to one invitation.
        with transaction.atomic():
            target = validated_invitation_user(request, lock=True)
            if target is None or (
                sociallogin.is_existing and sociallogin.user.pk != target.pk
            ):
                raise ImmediateHttpResponse(reject_invitation(request))
            if not sociallogin.is_existing:
                sociallogin.connect(request, target)
            clear_invitation(request)
