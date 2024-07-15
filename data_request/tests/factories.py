import factory

from lab.tests.factories import RunFactory

from ..models import DataRequest


class DataRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DataRequest

    user_first_name = factory.Faker("first_name")
    user_last_name = factory.Faker("last_name")
    user_email = factory.LazyAttribute(
        lambda u: f"{u.user_first_name}.{u.user_last_name}@example.com".lower()
    )
    user_institution = factory.Faker("company")
    description = factory.Faker("text")


class DataRequestWithRunsFactory(DataRequestFactory):
    @factory.post_generation
    def runs(obj: DataRequest, create: bool, *args, **kwargs):
        if not create:
            return
        for _ in range(3):
            obj.runs.add(RunFactory())  # pylint: disable=no-member
