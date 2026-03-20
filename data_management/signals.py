from django.db.models.signals import post_save
from django.dispatch import receiver

from lab.projects.models import Project, Run
from lab.runs.signals import run_scheduled

from .eligibility import sync_project_cooling_eligible_at
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
    sync_project_cooling_eligible_at(instance)


@receiver(post_save, sender=Run)
def update_project_eligibility_on_run_embargo_change(
    sender: type[Run],  # pylint: disable=unused-argument
    instance: Run,
    **kwargs,
) -> None:
    project_data = ProjectData.for_project(instance.project)

    if instance.embargo_date is not None and (
        project_data.cooling_eligible_at == instance.embargo_date
    ):
        return

    sync_project_cooling_eligible_at(instance.project)


@receiver(run_scheduled)
def update_project_eligibility_on_run_scheduled(
    sender: type[Run],  # pylint: disable=unused-argument
    instance: Run,
    **kwargs,
) -> None:
    """Update project eligibility when a run is scheduled."""
    sync_project_cooling_eligible_at(instance.project)
