# pylint: disable=no-member,unused-argument
from datetime import datetime
from typing import Literal

import graphene
from django.db.models import F, Sum
from django.utils import timezone

from .models import Object, ObjectGroup, Project, Run

StatPeriodLiteral = Literal["all", "year"]

THIS_YEAR_START_DT = datetime(timezone.now().year, 1, 1)


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
            return qs.filter(created__gte=THIS_YEAR_START_DT).count()
        return qs.count()

    @staticmethod
    def get_total_analyzed_objects(period: StatPeriodLiteral):
        run_qs = Run.objects.filter(end_date__lte=timezone.now())
        if period == "year":
            run_qs = run_qs.filter(start_date__gte=THIS_YEAR_START_DT)
        object_group_qs = ObjectGroup.objects.filter(runs__in=run_qs)
        object_qs = Object.objects.filter(group__in=object_group_qs)
        object_group_count = object_group_qs.count()
        object_count = object_qs.count()
        distinct_object_group_count = object_qs.values("group").distinct().count()
        return object_group_count + object_count - distinct_object_group_count

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
    stats = graphene.Field(LabStatsType)

    def resolve_stats(self, info):
        return {
            "all": LabStatType(
                total_projects=LabStatsType.get_total_projects("all"),
                total_object_groups=LabStatsType.get_total_analyzed_objects("all"),
                total_hours=LabStatsType.get_total_hours("all"),
            ),
            "year": LabStatType(
                total_projects=LabStatsType.get_total_projects("year"),
                total_object_groups=LabStatsType.get_total_analyzed_objects("year"),
                total_hours=LabStatsType.get_total_hours("year"),
            ),
        }


schema = graphene.Schema(query=Query)
