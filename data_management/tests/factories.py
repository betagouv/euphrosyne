import factory
from django.db.models.signals import post_save

from lab.tests.factories import ProjectFactory

from ..models import ProjectData


@factory.django.mute_signals(post_save)
class ProjectDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectData

    project = factory.SubFactory(ProjectFactory)
