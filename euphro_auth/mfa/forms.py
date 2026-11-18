from allauth.core import context
from allauth.mfa.totp import forms as totp_forms
from allauth.mfa.totp.internal.auth import SECRET_SESSION_KEY


class ActivateTOTPForm(totp_forms.ActivateTOTPForm):
    def __init__(self, *args, **kwargs) -> None:
        # allauth draws a new secret on every display of the page. Keep the one
        # already shown: another request reaching the page, such as the
        # browser's favicon request redirected here by the MFA gate, must not
        # invalidate the QR code being scanned.
        shown_secret = context.request.session.get(SECRET_SESSION_KEY)
        super().__init__(*args, **kwargs)
        if shown_secret:
            self.secret = context.request.session[SECRET_SESSION_KEY] = shown_secret
