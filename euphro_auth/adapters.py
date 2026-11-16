from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from shared.email_utils import use_user_language

LOCKOUT_MESSAGE = _(
    "Password sign-in is blocked for 15 minutes after too many failed attempts. "
    "You can still log in with ORCID."
)


class AccountAdapter(DefaultAccountAdapter):  # pylint: disable=abstract-method
    error_messages = {
        **DefaultAccountAdapter.error_messages,
        "too_many_login_attempts": LOCKOUT_MESSAGE,
    }

    def get_login_stages(self) -> list[str]:
        # Ask for the second factor only where MFA is enforced.
        return [
            (
                "euphro_auth.mfa.stages.AdminAuthenticateStage"
                if stage == "allauth.mfa.stages.AuthenticateStage"
                else stage
            )
            for stage in super().get_login_stages()
        ]

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        # Accounts are created by administrators, or by invitation.
        return False

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        # Every allauth email (password reset, security notices) is written in
        # the language of the account it is about.
        with use_user_language(user=context.get("user")):
            super().send_mail(template_prefix, email, context)

    def send_notification_mail(
        self,
        template_prefix: str,
        user,
        context: dict[str, Any] | None = None,
        email: str | None = None,
    ) -> None:
        # User.email is the account address (allauth may hold no EmailAddress
        # row for it). The client IP address is left out of the notices: behind
        # the hosting router it is not the user's.
        super().send_notification_mail(
            template_prefix,
            user,
            {
                "user": user,
                "email": user.email,
                "site_url": settings.SITE_URL,
                **(context or {}),
            },
            email=email or user.email,
        )
