from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpRequest

from . import password_lockout


def _credential_email(credentials: dict[str, Any]) -> str | None:
    email = credentials.get("email") or credentials.get("username")
    return email if isinstance(email, str) and email else None


# Phone methods are not used: accounts sign in by email.
class AccountAdapter(DefaultAccountAdapter):  # pylint: disable=abstract-method
    error_messages = {
        **DefaultAccountAdapter.error_messages,
        "too_many_login_attempts": password_lockout.LOCKOUT_MESSAGE,
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

    def pre_authenticate(self, request: HttpRequest, **credentials: Any) -> None:
        # Replaces allauth's own login_failed check, keyed by site and email,
        # with the lockout rules of euphro_auth.password_lockout.
        # allauth rolls this usage back after a successful authentication.
        # pylint: disable=attribute-defined-outside-init
        self._login_failed_rl_usage = None
        email = _credential_email(credentials)
        if email is None:
            return
        if password_lockout.is_locked_out(request, email):
            raise self.validation_error("too_many_login_attempts")
        self._login_failed_rl_usage = password_lockout.consume_attempt(request, email)
        if not self._login_failed_rl_usage:
            raise self.validation_error("too_many_login_attempts")

    def authenticate(self, request: HttpRequest, **credentials: Any):
        user = super().authenticate(request, **credentials)
        email = _credential_email(credentials)
        if user is not None and email is not None:
            password_lockout.reset_failures(request, email)
        return user

    def authentication_failed(self, request: HttpRequest, **credentials: Any) -> None:
        email = _credential_email(credentials)
        if email is not None and password_lockout.record_failure(request, email):
            raise self.validation_error("too_many_login_attempts")
