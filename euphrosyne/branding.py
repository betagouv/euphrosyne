from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class Branding:
    facility_name: str
    facility_url: str


def get_branding() -> Branding:
    return Branding(
        facility_name=settings.FACILITY_NAME,
        facility_url=settings.FACILITY_URL,
    )
