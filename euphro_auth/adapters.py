import logging
import time

from allauth.account import app_settings as account_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.internal.flows.login import get_authentication_records
from allauth.account.internal.flows.reauthentication import (
    get_reauthentication_flows,
)
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .mfa import services as mfa_services
from .signals import describe_account

logger = logging.getLogger(__name__)

LOCKOUT_MESSAGE = _(
    "Password sign-in is blocked for 15 minutes after too many failed attempts. "
    "You can still log in with ORCID."
)


class AccountAdapter(DefaultAccountAdapter):  # pylint: disable=abstract-method
    error_messages = {
        **DefaultAccountAdapter.error_messages,
        "too_many_login_attempts": LOCKOUT_MESSAGE,
    }

    def pre_authenticate(self, request: HttpRequest, **credentials) -> None:
        # The password is not checked once locked out, so Django sends no
        # `user_login_failed` signal: log the refusal here.
        try:
            super().pre_authenticate(request, **credentials)
        except ValidationError as error:
            if error.code == "too_many_login_attempts":
                logger.warning(
                    "Password sign-in refused for %s (%s)",
                    describe_account(
                        credentials.get("email") or credentials.get("username")
                    ),
                    error.code,
                )
            raise

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

    def is_reauthentication_required(self, *, app: str, **kwargs) -> bool:
        # Accounts with no way to reauthenticate (ORCID only, no second factor
        # yet) would be refused, and an administrator could then never set up
        # the second factor the gate requires. They have just signed in
        # through ORCID.
        user = self.request.user
        if user.is_authenticated and not get_reauthentication_flows(user):
            return False
        # Enrolling a first factor right after signing in with the password:
        # asking for the password again would be a second prompt for nothing.
        # Removing a factor still asks (the user then has one).
        if (
            user.is_authenticated
            and not mfa_services.has_totp(user)
            and self._signed_in_with_password_recently(user)
        ):
            return False
        return super().is_reauthentication_required(app=app, **kwargs)

    def _signed_in_with_password_recently(self, user) -> bool:
        timeout = account_settings.REAUTHENTICATION_TIMEOUT
        return any(
            record.get("method") == "password"
            and time.time() - record.get("at", 0) < timeout
            for record in get_authentication_records(self.request, user)
        )
