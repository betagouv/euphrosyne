from lab.models import Institution
from radiation_protection.app_settings import settings as app_settings


def should_exempt_institution(institution: Institution | None = None) -> bool:
    exempt_ror_ids = (
        app_settings.RADIATION_PROTECTION_ELECTRICAL_SIGNATURE_EXEMPT_ROR_IDS  # type: ignore[misc] # pylint: disable=line-too-long
    )
    institution_ror_id = institution.ror_id if institution else None
    if not exempt_ror_ids or not institution_ror_id:
        return False
    return institution_ror_id in exempt_ror_ids
