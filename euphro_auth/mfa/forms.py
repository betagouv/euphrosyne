"""allauth MFA forms that log failed codes with the consecutive failure count."""

from allauth.mfa.base import forms as base_forms
from allauth.mfa.totp import forms as totp_forms
from django.core.exceptions import ValidationError

from ..models import User
from . import services


class LogFailuresMixin:
    failure_step = "verification"
    user: User

    def clean_code(self) -> str:
        try:
            return super().clean_code()  # type: ignore[misc]
        except ValidationError:
            services.record_failure(self.user, self.failure_step)
            raise


class AuthenticateForm(LogFailuresMixin, base_forms.AuthenticateForm):
    pass


class ReauthenticateForm(LogFailuresMixin, base_forms.ReauthenticateForm):
    pass


class ActivateTOTPForm(LogFailuresMixin, totp_forms.ActivateTOTPForm):
    failure_step = "enrollment"
