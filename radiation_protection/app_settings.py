import os
from typing import List, Optional

from shared.app_settings import AppLazySettings, connect_reload_signal


def _split_emails(value: str) -> List[str]:
    return [email for email in value.split(",") if email]


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

settings = AppLazySettings()
connect_reload_signal(settings)
