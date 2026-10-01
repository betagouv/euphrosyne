from typing import Any

from django.conf import settings
from django.shortcuts import redirect
from social_core.backends.orcid import ORCIDOAuth2 as SocialORCIDOAuth2
from social_core.storage import PartialMixin, UserProtocol
from social_core.strategy import HttpResponseProtocol
from social_django.strategy import DjangoStrategy

from .invitations import (
    INVITATION_SESSION_KEY,
    clear_registration,
    reject_invitation,
    validated_invitation_user,
    validated_registration_partial,
)


class ORCIDOAuth2(SocialORCIDOAuth2):  # pylint: disable=abstract-method
    strategy: DjangoStrategy
    BASE_DOMAIN = "sandbox.orcid.org" if settings.ORCID_USE_SANDBOX else "orcid.org"

    AUTHORIZATION_URL = f"https://{BASE_DOMAIN}/oauth/authorize"
    ACCESS_TOKEN_URL = f"https://{BASE_DOMAIN}/oauth/token"
    USER_ID_URL = f"https://{BASE_DOMAIN}/oauth/userinfo"
    USER_DATA_URL = f"https://pub.{BASE_DOMAIN}/v2.0/" + "{}"

    def get_key_and_secret(self):
        return (
            getattr(settings, "SOCIAL_AUTH_ORCID_KEY"),
            getattr(settings, "SOCIAL_AUTH_ORCID_SECRET"),
        )

    def start(self) -> HttpResponseProtocol:
        request = self.strategy.request
        if INVITATION_SESSION_KEY in request.session:
            if validated_invitation_user(request) is None:
                return reject_invitation(request)
        clear_registration(request)
        # A fresh state binds the invitation to this OAuth attempt, including
        # when another invitation link is opened in the same browser meanwhile.
        self.strategy.session_pop("orcid_state")
        response = super().start()
        context = request.session.get(INVITATION_SESSION_KEY)
        if context:
            request.session[INVITATION_SESSION_KEY] = {
                **context,
                "oauth_state": self.get_session_state(),
            }
        return response

    def auth_complete(
        self, *args: Any, **kwargs: Any
    ) -> UserProtocol | HttpResponseProtocol | None:
        request = self.strategy.request
        if INVITATION_SESSION_KEY in request.session:
            if validated_invitation_user(request, for_callback=True) is None:
                return reject_invitation(request)
        return super().auth_complete(*args, **kwargs)

    def continue_pipeline(
        self, partial: PartialMixin
    ) -> UserProtocol | HttpResponseProtocol | None:
        request = self.strategy.request
        validated = validated_registration_partial(request, partial.token)
        if validated is None or (
            partial.kwargs.get("user") != validated.kwargs.get("user")
            or partial.kwargs.get("social") != validated.kwargs.get("social")
        ):
            return reject_invitation(request)
        if not validated.kwargs["user"].invitation_completed_at:
            return redirect("complete_registration_orcid", token=partial.token)
        response = super().continue_pipeline(partial)
        clear_registration(request)
        return response
