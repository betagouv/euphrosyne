# pylint: disable=no-member,unused-argument
import itertools
from datetime import datetime
from typing import Literal

import graphene
from django.db.models import F, Prefetch, Q, Sum
from django.utils import timezone
from graphene_django import DjangoObjectType

from euphro_auth.models import User

from .methods.dto import method_model_to_dto
from .models import Institution, Object, ObjectGroup, Participation, Project, Run

StatPeriodLiteral = Literal["all", "year"]

THIS_YEAR_START_DT = datetime(timezone.now().year, 1, 1)


class ObjectType(DjangoObjectType):
    class Meta:
        model = Object
        fields = ("label", "collection")


class ObjectGroupType(DjangoObjectType):
    data_available = graphene.Boolean(required=True)

    class Meta:
        model = ObjectGroup
        fields = (
            "id",
            "c2rmf_id",
            "label",
            "materials",
            "discovery_place",
            "collection",
            "dating",
            "object_set",
            "runs",
            "data_available",
            "created",
        )

    def resolve_data_available(self, info):
        if not hasattr(self, "is_data_available"):
            raise AttributeError(
                "is_data_available must be annotated on the queryset in the \
                Quey section (lab.schema.Query). See \
                https://docs.djangoproject.com/en/4.2/topics/db/aggregation/"
            )
        return self.is_data_available


class InstitutionType(DjangoObjectType):
    class Meta:
        model = Institution
        fields = ("name", "country")


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class LeaderType(DjangoObjectType):
    class Meta:
        model = Participation
        fields = ("user", "institution")


class DetectorType(graphene.ObjectType):
    name = graphene.String(required=True)
    enabled = graphene.Boolean(required=True)
    filters = graphene.List(graphene.String, required=True)


class MethodType(graphene.ObjectType):
    name = graphene.String(required=True)
    enabled = graphene.Boolean(required=True)
    detectors = graphene.List(DetectorType, required=True)


class RunType(DjangoObjectType):
    methods = graphene.List(MethodType)

    class Meta:
        model = Run
        fields = (
            "label",
            "start_date",
            "particle_type",
            "energy_in_keV",
            "beamline",
            "methods",
            "project",
        )

    def resolve_methods(self, info):
        methods = []
        for method_dto in method_model_to_dto(self):
            method = MethodType(name=method_dto.name, detectors=[])
            for detector_dto in method_dto.detectors:
                method.detectors.append(
                    DetectorType(
                        name=detector_dto.name,
                        filters=detector_dto.filters,
                    )
                )
            methods.append(method)
        return methods


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        fields = (
            "name",
            "status",
            "comments",
            "runs",
            "leader",
            "object_groups",
            "slug",
            "created",
        )

    object_group_materials = graphene.List(graphene.String)
    status = graphene.String()
    leader = graphene.Field(LeaderType)
    object_groups = graphene.List(ObjectGroupType)

    def resolve_status(self, info):
        return self.status

    def resolve_object_group_materials(self, info):
        project_materials = ObjectGroup.objects.filter(runs__project=self).values_list(
            "materials", flat=True
        )
        return set(itertools.chain(*project_materials))

    def resolve_leader(self, info):
        return self.leader

    def resolve_object_groups(self, info):
        return list(
            set(
                objectgroup
                for run in self.runs.all()
                for objectgroup in run.run_object_groups.all()
            )
        )


class LabStatType(graphene.ObjectType):
    total_projects = graphene.Int()
    total_object_groups = graphene.Int()
    total_hours = graphene.Int()


class LabStatField(graphene.Field):
    period: StatPeriodLiteral

    def __init__(self, *args, period: StatPeriodLiteral = "all", **kwargs):
        self.period = period
        super().__init__(LabStatType, *args, **kwargs)


class LabStatsType(graphene.ObjectType):
    all = LabStatField(period="all")
    year = LabStatField(period="year")

    @staticmethod
    def get_total_projects(period: StatPeriodLiteral):
        qs = Project.objects
        if period == "year":
            qs = qs.filter(created__gte=THIS_YEAR_START_DT)
        print(THIS_YEAR_START_DT)
        return qs.count()

    @staticmethod
    def get_total_object_groups(period: StatPeriodLiteral):
        run_qs = Run.objects.filter(end_date__lte=timezone.now())
        if period == "year":
            run_qs = run_qs.filter(start_date__gte=THIS_YEAR_START_DT)
        return ObjectGroup.objects.filter(runs__in=run_qs).count()

    @staticmethod
    def get_total_hours(period: StatPeriodLiteral):
        qs = Run.objects.filter(end_date__lte=timezone.now())
        if period == "year":
            qs = qs.filter(start_date__gte=THIS_YEAR_START_DT)
        qs = qs.annotate(time_in_secs=(F("end_date") - F("start_date")))
        aggregation = qs.aggregate(total_hours=Sum("time_in_secs"))
        if not aggregation.get("total_hours"):
            return 0
        return int(aggregation["total_hours"].total_seconds() / 3600)


class Query(graphene.ObjectType):
    last_projects = graphene.List(ProjectType, limit=graphene.Int())
    project_detail = graphene.Field(ProjectType, slug=graphene.String())
    object_group_detail = graphene.Field(ObjectGroupType, pk=graphene.String())
    stats = graphene.Field(LabStatsType)

    def resolve_last_projects(self, info, limit=None):
        projects = (
            Project.objects.only_finished()
            .only_public()
            .order_by("-created")
            .distinct()
        )
        if limit:
            projects = projects[:limit]
        return projects

    def resolve_project_detail(self, _, slug):
        return (
            Project.objects.only_finished()
            .prefetch_related(
                "runs",
                "runs__run_object_groups",
                "runs__run_object_groups__object_set",
            )
            .filter(slug=slug)
            .first()
        )

    def resolve_object_group_detail(self, _, pk):  # pylint: disable=invalid-name
        return (
            ObjectGroup.objects.filter(pk=pk)
            .prefetch_related(Prefetch("runs", queryset=Run.objects.only_finished()))
            .annotate(is_data_available=Q(runs__project__is_data_available=True))
            .first()
        )

    def resolve_stats(self, info):
        return {
            "all": LabStatType(
                total_projects=LabStatsType.get_total_projects("all"),
                total_object_groups=LabStatsType.get_total_object_groups("all"),
                total_hours=LabStatsType.get_total_hours("all"),
            ),
            "year": LabStatType(
                total_projects=LabStatsType.get_total_projects("year"),
                total_object_groups=LabStatsType.get_total_object_groups("year"),
                total_hours=LabStatsType.get_total_hours("year"),
            ),
        }


schema = graphene.Schema(query=Query)
