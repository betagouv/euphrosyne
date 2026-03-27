from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from lab.projects.models import Project

    from .models import ProjectData

COOLING_DELAY_DAYS = 30 * 24
COOLING_DELAY_DELTA = timedelta(days=COOLING_DELAY_DAYS)


def _datetime_to_date(value: datetime) -> date:
    if timezone.is_naive(value):
        return value.date()
    return timezone.localdate(value)


def _run_cooling_eligible_at(
    *, end_date: datetime | None, embargo_date: date | None
) -> date | None:
    if embargo_date is not None:
        return embargo_date
    if end_date is not None:
        return _datetime_to_date(end_date + COOLING_DELAY_DELTA)
    return None


def compute_cooling_eligible_at(project: Project) -> date:
    """Compute cooling eligibility from the latest per-run eligibility date."""
    cooling_eligible_at = max(
        (
            candidate
            for end_date, embargo_date in project.runs.values_list(
                "end_date", "embargo_date"
            )
            if (
                candidate := _run_cooling_eligible_at(
                    end_date=end_date,
                    embargo_date=embargo_date,
                )
            )
            is not None
        ),
        default=None,
    )
    if cooling_eligible_at is not None:
        return cooling_eligible_at

    created_at = project.created or timezone.now()
    return _datetime_to_date(created_at + COOLING_DELAY_DELTA)


def sync_project_cooling_eligible_at(project: Project) -> ProjectData:
    from .models import ProjectData  # pylint: disable=import-outside-toplevel

    cooling_eligible_at = compute_cooling_eligible_at(project)
    try:
        project_data = project.project_data
    except ProjectData.DoesNotExist:
        project_data, _ = ProjectData.objects.get_or_create(
            project=project,
            defaults={"cooling_eligible_at": cooling_eligible_at},
        )

    if project_data.cooling_eligible_at != cooling_eligible_at:
        project_data.cooling_eligible_at = cooling_eligible_at
        project_data.save(update_fields=["cooling_eligible_at"])

    return project_data
