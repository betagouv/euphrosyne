from allauth.mfa.stages import AuthenticateStage

from .services import is_mfa_required, remove_unreadable_factors


class AdminAuthenticateStage(AuthenticateStage):
    """Ask for the second factor at sign-in only where MFA is enforced
    (administrators, unless MFA_ADMIN_REQUIRED is off)."""

    def handle(self) -> tuple:
        if is_mfa_required(self.login.user):
            # After a SECRET_KEY change: the user sets up a new factor.
            remove_unreadable_factors(self.login.user)
        return super().handle()

    def _should_handle(self, request) -> bool:
        return is_mfa_required(self.login.user) and super()._should_handle(request)
