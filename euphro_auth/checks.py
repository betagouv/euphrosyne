from django.conf import settings
from django.core.checks import Error, register


@register()
def check_totp_encryption_keys(app_configs, **kwargs):
    # pylint: disable=unused-argument,import-outside-toplevel
    from cryptography.fernet import Fernet

    keys = settings.MFA_TOTP_ENCRYPTION_KEYS
    if not keys:
        return [
            Error(
                "MFA_TOTP_ENCRYPTION_KEYS is not set: TOTP secrets cannot be "
                "encrypted.",
                hint="Generate a key with "
                "`python -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'`.",
                id="euphro_auth.E001",
            )
        ]
    try:
        for key in keys:
            Fernet(key.encode())
    except ValueError:
        return [
            Error(
                "MFA_TOTP_ENCRYPTION_KEYS holds an invalid Fernet key.",
                id="euphro_auth.E002",
            )
        ]
    return []
