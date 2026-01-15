import os
from typing import List, Optional

from shared.app_settings import AppLazySettings, connect_reload_signal


def _split_emails(value: str) -> List[str]:
    return [email for email in value.split(",") if email]


def _split_values(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


RADIATION_PROTECTION_TALLY_SECRET_KEY: Optional[str] = os.getenv(
    "RADIATION_PROTECTION_TALLY_SECRET_KEY"
)
RADIATION_PROTECTION_RISK_ADVISOR_EMAIL: Optional[str] = os.getenv(
    "RADIATION_PROTECTION_RISK_ADVISOR_EMAIL"
)
RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME: str = os.getenv(
    "RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME", ""
)
RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS: List[str] = _split_emails(
    os.environ.get("RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS", "")
)
RADIATION_PROTECTION_ELECTRICAL_SIGNATURE_EXEMPT_ROR_IDS: List[str] = _split_values(
    os.environ.get("RADIATION_PROTECTION_ELECTRICAL_SIGNATURE_EXEMPT_ROR_IDS", "")
)

GOODFLAG_API_BASE = os.getenv("GOODFLAG_API_BASE")
GOODFLAG_API_TOKEN = os.getenv("GOODFLAG_API_TOKEN")
GOODFLAG_USER_ID = os.getenv("GOODFLAG_USER_ID")
GOODFLAG_SIGNATURE_CONSENT_PAGE_ID = os.getenv("GOODFLAG_SIGNATURE_CONSENT_PAGE_ID")
GOODFLAG_SIGNATURE_PROFILE_ID = os.getenv("GOODFLAG_SIGNATURE_PROFILE_ID")

settings = AppLazySettings()
connect_reload_signal(settings)
