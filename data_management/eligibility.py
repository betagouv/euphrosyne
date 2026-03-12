from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from django.db.models import Max
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


def compute_cooling_eligible_at(project: Project) -> date:
    """Compute cooling eligibility with embargo dates taking precedence."""
    run_dates = project.runs.aggregate(
        latest_embargo_date=Max("embargo_date"),
        latest_end_date=Max("end_date"),
    )
    latest_embargo_date: date | None = run_dates["latest_embargo_date"]
    if latest_embargo_date is not None:
        return latest_embargo_date

    latest_end_date: datetime | None = run_dates["latest_end_date"]
    if latest_end_date is not None:
        return _datetime_to_date(latest_end_date + COOLING_DELAY_DELTA)

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
