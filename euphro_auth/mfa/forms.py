"""allauth MFA forms that log failed codes with the consecutive failure count."""

from allauth.core import context
from allauth.mfa.base import forms as base_forms
from allauth.mfa.totp import forms as totp_forms
from allauth.mfa.totp.internal.auth import SECRET_SESSION_KEY
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

    def __init__(self, *args, **kwargs) -> None:
        # allauth draws a new secret on every display of the page. Keep the one
        # already shown: another request reaching the page, such as the
        # browser's favicon request redirected here by the MFA gate, must not
        # invalidate the QR code being scanned.
        shown_secret = context.request.session.get(SECRET_SESSION_KEY)
        super().__init__(*args, **kwargs)
        if shown_secret:
            self.secret = context.request.session[SECRET_SESSION_KEY] = shown_secret
