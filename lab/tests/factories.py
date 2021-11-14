import factory

from ..models import Project, Run


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Run {n}")


class RunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Run

    label = factory.Sequence(lambda n: "Run {n}")
    project = factory.SubFactory(ProjectFactory)
