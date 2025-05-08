from datetime import datetime
from typing import Literal

from django.db.models import F, Sum
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import Object, ObjectGroup, Project, Run

StatPeriodLiteral = Literal["all", "year"]

THIS_YEAR_START_DT = datetime(
    timezone.now().year, 1, 1, tzinfo=timezone.get_current_timezone()
)


class LabStatsSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    total_projects = serializers.IntegerField()
    total_object_groups = serializers.IntegerField()
    total_hours = serializers.IntegerField()


class StatsResponse(serializers.Serializer):  # pylint: disable=abstract-method
    all = LabStatsSerializer()
    year = LabStatsSerializer()


class LabStatsUtils:
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


@api_view(["GET"])
def stats_view(request):
    stats = {
        "all": {
            "total_projects": LabStatsUtils.get_total_projects("all"),
            "total_object_groups": LabStatsUtils.get_total_analyzed_objects("all"),
            "total_hours": LabStatsUtils.get_total_hours("all"),
        },
        "year": {
            "total_projects": LabStatsUtils.get_total_projects("year"),
            "total_object_groups": LabStatsUtils.get_total_analyzed_objects("year"),
            "total_hours": LabStatsUtils.get_total_hours("year"),
        },
    }
    serializer = StatsResponse(stats)
    return Response(serializer.data)
