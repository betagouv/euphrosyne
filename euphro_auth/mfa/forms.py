"""allauth MFA forms that log failed codes with the consecutive failure count."""

from allauth.mfa.base import forms as base_forms
from allauth.mfa.totp import forms as totp_forms
from django.core.exceptions import ValidationError

from . import services


class AuthenticateForm(base_forms.AuthenticateForm):
    def clean_code(self) -> str:
        try:
            return super().clean_code()
        except ValidationError:
            services.record_failure(self.user, "verification")
            raise


class ReauthenticateForm(base_forms.ReauthenticateForm):
    def clean_code(self) -> str:
        try:
            return super().clean_code()
        except ValidationError:
            services.record_failure(self.user, "verification")
            raise


class ActivateTOTPForm(totp_forms.ActivateTOTPForm):
    def clean_code(self) -> str:
        try:
            return super().clean_code()
        except ValidationError:
            services.record_failure(self.user, "enrollment")
            raise
