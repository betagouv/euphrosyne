from datetime import datetime, timedelta, timezone

import factory
import factory.fuzzy

from euphro_auth.tests.factories import StaffUserFactory
from lab.thesauri.models import Era

from ..models import Object, ObjectGroup, Participation, Period, Project, Run
from ..objects.models import Location

NOW = datetime.now(tz=timezone.utc)


class ParticipationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Participation

    user = factory.SubFactory(StaffUserFactory)
    project = factory.SubFactory("lab.tests.factories.ProjectFactory")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Faker("name")


class ProjectWithLeaderFactory(ProjectFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    leader_participation = factory.RelatedFactory(
        ParticipationFactory, factory_related_name="project", is_leader=True
    )


class FinishedProject(ProjectFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    @factory.post_generation
    def runs(self, create, *args, **kwargs):
        if not create:
            return
        RunFactory(
            project=self,
            start_date=NOW - timedelta(days=2),
            end_date=NOW - timedelta(days=1),
            embargo_date=NOW - timedelta(days=1),
        )


class ProjectWithMultipleParticipationsFactory(ProjectWithLeaderFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    member_1 = factory.RelatedFactory(
        ParticipationFactory, factory_related_name="project", is_leader=False
    )
    member_2 = factory.RelatedFactory(
        ParticipationFactory, factory_related_name="project", is_leader=False
    )
    member_3 = factory.RelatedFactory(
        ParticipationFactory, factory_related_name="project", is_leader=False
    )
    member_4 = factory.RelatedFactory(
        ParticipationFactory, factory_related_name="project", is_leader=False
    )


class RunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Run

    label = factory.Faker("name")
    project = factory.SubFactory(ProjectFactory)
    energy_in_keV = factory.fuzzy.FuzzyInteger(0, high=10000, step=500)
    particle_type = factory.fuzzy.FuzzyChoice(Run.ParticleType)
    start_date = factory.fuzzy.FuzzyDateTime(
        start_dt=NOW, end_dt=NOW + timedelta(days=1)
    )
    end_date = factory.fuzzy.FuzzyDateTime(
        start_dt=NOW + timedelta(days=7), end_dt=NOW + timedelta(days=8)
    )
    embargo_date = factory.fuzzy.FuzzyDate(
        start_date=NOW.date() + timedelta(days=15),
        end_date=NOW.date() + timedelta(days=21),
    )
    beamline = "Microbeam"


class RunForceNoMethodFactory(RunFactory):
    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        method_fieldnames = [f.name for f in Run.get_method_fields()]
        return {
            fieldname: value
            for fieldname, value in kwargs.items()
            if fieldname not in method_fieldnames
        }


class NotEmbargoedRun(RunFactory):
    embargo_date = NOW.date() - timedelta(days=1)


class RunReadyToAskExecFactory(RunFactory):
    # pylint: disable=no-member
    status = Run.Status.CREATED.value
    method_PIXE = True


class PeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Period

    label = factory.Faker("date")


class EraFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Era

    label = factory.Faker("date")


class ObjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Object

    label = factory.Faker("words")


class ObjectGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ObjectGroup
        skip_postgeneration_save = True

    label = factory.Faker("name")
    dating_period = factory.SubFactory(PeriodFactory)
    dating_era = factory.SubFactory(EraFactory)
    materials = factory.fuzzy.FuzzyChoice(["wood", "stone", "glass", "metal"], list)
    object_count = 3

    @factory.post_generation
    def objects(self, *args, **kwargs):
        return ObjectFactory.create_batch(3, group_id=self.id)


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    label = factory.Faker("name")
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
