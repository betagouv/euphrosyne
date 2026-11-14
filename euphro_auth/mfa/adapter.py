"""Encryption at rest of TOTP secrets (R13).

allauth stores each TOTP secret in ``Authenticator.data["secret"]`` and passes
it through its MFA adapter's ``encrypt``/``decrypt`` hooks. Secrets are
encrypted with Fernet (AES-128-CBC and HMAC-SHA256) using the keys of
MFA_TOTP_ENCRYPTION_KEYS: the first encrypts, every key decrypts, so keys can
be rotated (``manage.py rotate_totp_keys``)."""

from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings

PREFIX = "fernet:"


def get_fernet() -> MultiFernet:
    return MultiFernet(
        [Fernet(key.encode()) for key in settings.MFA_TOTP_ENCRYPTION_KEYS]
    )


class MFAAdapter(DefaultMFAAdapter):
    def encrypt(self, text: str) -> str:
        return PREFIX + get_fernet().encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text.startswith(PREFIX):
            raise ValueError("TOTP secret is not encrypted.")
        token = encrypted_text.removeprefix(PREFIX).encode()
        return get_fernet().decrypt(token).decode()


def rotate(encrypted_text: str) -> str:
    """Re-encrypt with the first key."""
    token = encrypted_text.removeprefix(PREFIX).encode()
    return PREFIX + get_fernet().rotate(token).decode()
