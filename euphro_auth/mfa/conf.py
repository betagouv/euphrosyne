"""MFA configuration helpers.

Imported by the settings module: must not import models.
"""

import logging

logger = logging.getLogger(__name__)

FALSE_VALUES = {"0", "false", "no", "off"}


def parse_mfa_admin_required(value: str | None) -> bool:
    """MFA stays enforced unless the value is explicitly false.

    Unset, empty or unrecognised values keep it on (fail closed)."""
    if value is None:
        return True
    return value.strip().lower() not in FALSE_VALUES


def warn_if_mfa_disabled() -> None:
    # pylint: disable=import-outside-toplevel
    from django.conf import settings

    if not settings.MFA_ADMIN_REQUIRED:
        logger.warning(
            "MFA_ADMIN_REQUIRED is off: multi-factor authentication is NOT "
            "enforced for administrators."
        )
