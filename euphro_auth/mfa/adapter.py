"""Encryption at rest of TOTP secrets (R13).

allauth stores each TOTP secret in ``Authenticator.data["secret"]`` and passes
it through its MFA adapter's ``encrypt``/``decrypt`` hooks. Secrets are
encrypted with Fernet (AES-128-CBC and HMAC-SHA256), with a key derived from
SECRET_KEY. SECRET_KEY_FALLBACKS are deliberately not used: after a SECRET_KEY
change, the secrets can no longer be read and administrators set up a new
factor at their next sign-in."""

import base64

from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.utils.crypto import salted_hmac

PREFIX = "fernet:"
KEY_SALT = "euphro_auth.mfa.totp_secret"


def get_fernet() -> Fernet:
    key = salted_hmac(
        KEY_SALT, "", secret=settings.SECRET_KEY, algorithm="sha256"
    ).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class MFAAdapter(DefaultMFAAdapter):
    def encrypt(self, text: str) -> str:
        return PREFIX + get_fernet().encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text.startswith(PREFIX):
            raise ValueError("TOTP secret is not encrypted.")
        token = encrypted_text.removeprefix(PREFIX).encode()
        return get_fernet().decrypt(token).decode()


def is_readable(encrypted_text: str) -> bool:
    try:
        MFAAdapter().decrypt(encrypted_text)
    except (InvalidToken, ValueError):
        return False
    return True
