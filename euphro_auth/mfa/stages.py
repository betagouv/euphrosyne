from allauth.mfa.stages import AuthenticateStage

from .services import is_mfa_required, remove_unreadable_factors


class AdminAuthenticateStage(AuthenticateStage):
    """Ask for the second factor at sign-in only where MFA is enforced
    (administrators, unless MFA_ADMIN_REQUIRED is off)."""

    def _should_handle(self, request) -> bool:
        if not is_mfa_required(self.login.user):
            return False
        remove_unreadable_factors(self.login.user)
        return super()._should_handle(request)
