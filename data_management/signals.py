from datetime import timedelta

from django.db.models import DateTimeField, ExpressionWrapper, F, Subquery, Value
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver

from lab.projects.models import Project, Run
from lab.runs.signals import run_scheduled

from .models import ProjectData


@receiver(post_save, sender=Project)
def ensure_project_data_exists(
    sender: type[Project],  # pylint: disable=unused-argument
    instance: Project,
    created: bool,
    **kwargs,
) -> None:
    if not created:
        return
    ProjectData.for_project(instance)


@receiver(run_scheduled)
def update_project_eligibility_on_run_scheduled(
    sender: type[Run],  # pylint: disable=unused-argument
    instance: Run,
    **kwargs,
) -> None:
    """Update project eligibility when a run is scheduled.

    Eligibility follows the latest end_date across all project runs.
    """
    latest_end_date = Subquery(
        instance.project.runs.filter(end_date__isnull=False)
        .order_by("-end_date")
        .values("end_date")[:1]
    )
    project_data = ProjectData.for_project(instance.project)
    project_data_qs = ProjectData.objects.filter(pk=project_data.pk)
    eligible_at = ExpressionWrapper(
        latest_end_date + Value(timedelta(days=30 * 6)),
        output_field=DateTimeField(),
    )
    project_data_qs.update(
        cooling_eligible_at=Coalesce(
            eligible_at,
            F("cooling_eligible_at"),
            output_field=DateTimeField(),
        )
    )
