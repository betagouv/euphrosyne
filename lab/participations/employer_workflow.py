from django.apps import apps
from django.conf import settings
from django.urls import reverse

from .models import Participation


def _is_employer_workflow_enabled() -> bool:
    return apps.is_installed("radiation_protection")


def _is_employer_exempt_participation(participation: Participation) -> bool:
    institution = participation.institution
    ror_id = institution.ror_id if institution else None
    return bool(
        ror_id and ror_id in settings.PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS
    )


def is_incomplete_on_premises_participation(participation: Participation) -> bool:
    if not _is_employer_workflow_enabled():
        return False
    if not participation.on_premises:
        return False
    if participation.employer_id:
        return False
    return not _is_employer_exempt_participation(participation)


def get_incomplete_participation_for_user(
    user, project_id: int
) -> Participation | None:
    if not _is_employer_workflow_enabled() or not user.is_authenticated:
        return None
    if getattr(user, "is_lab_admin", False) or getattr(user, "is_superuser", False):
        return None
    try:
        participation = Participation.objects.select_related(
            "institution", "employer"
        ).get(user=user, project_id=project_id)
    except Participation.DoesNotExist:
        return None
    if participation and is_incomplete_on_premises_participation(participation):
        return participation
    return None


def get_employer_completion_url(project_id: int) -> str:
    return reverse(
        "participation_employer_completion", kwargs={"project_id": project_id}
    )
