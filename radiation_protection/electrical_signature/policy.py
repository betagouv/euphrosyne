from django.conf import settings

from lab.models import Institution
from lab.participations.models import Participation


def should_exempt_institution(institution: Institution | None = None) -> bool:
    """Return whether the institution is exempt from employer/signature workflow."""
    exempt_ror_ids = settings.PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS
    institution_ror_id = institution.ror_id if institution else None
    if not institution_ror_id:
        return False
    return institution_ror_id in exempt_ror_ids


def participation_has_required_employer_for_risk_prevention(
    participation: Participation,
) -> bool:
    return bool(participation.employer_id) or should_exempt_institution(
        participation.institution
    )
