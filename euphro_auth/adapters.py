from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.internal.flows.reauthentication import (
    get_reauthentication_flows,
)
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

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

    def is_reauthentication_required(self, *, app: str, **kwargs) -> bool:
        # An ORCID-only account (no password, no second factor yet) has no
        # way to reauthenticate: allauth 65.22 would refuse it, and an
        # administrator could then never set up the second factor that
        # AccountGatesMiddleware requires. Such users signed in through ORCID
        # just before, as allauth 65.21 assumed.
        user = self.request.user
        if user.is_authenticated and not get_reauthentication_flows(user):
            return False
        return super().is_reauthentication_required(app=app, **kwargs)
