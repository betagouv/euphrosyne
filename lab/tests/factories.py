import factory
from django.contrib.auth import get_user_model

from ..models import AnalysisTechniqueUsed, Project, Run


class StaffUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda u: "{}.{}@example.com".format(u.first_name, u.last_name).lower()
    )
    password = factory.Faker("password")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")


class RunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Run

    label = factory.Sequence(lambda n: "Run {n}")
    project = factory.SubFactory(ProjectFactory)


class AnalysisTechniqueUsedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnalysisTechniqueUsed

    run = factory.SubFactory(Run)
