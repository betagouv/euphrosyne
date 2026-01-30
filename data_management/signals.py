from django.db.models.signals import post_save
from django.dispatch import receiver

from lab.projects.models import Project

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
