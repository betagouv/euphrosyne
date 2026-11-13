from allauth.account.forms import EmailAwarePasswordResetTokenGenerator
from django.conf import settings
from django.utils.http import base36_to_int


class PasswordResetTokenGenerator(EmailAwarePasswordResetTokenGenerator):
    """allauth's password reset tokens, valid for PASSWORD_RESET_LINK_TIMEOUT.

    Django's PASSWORD_RESET_TIMEOUT still applies to invitation links, which use
    Django's default token generator."""

    def check_token(self, user, token) -> bool:
        if not super().check_token(user, token):
            return False
        timestamp = base36_to_int(token.split("-")[0])
        age = self._num_seconds(self._now()) - timestamp
        return age <= settings.PASSWORD_RESET_LINK_TIMEOUT
