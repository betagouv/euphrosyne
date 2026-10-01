from django.shortcuts import get_object_or_404
from rest_framework import generics

from ...api_views.permissions import ProjectMembershipRequiredMixin
from ...projects.models import Project
from ...runs.models import Run
from ..models import MeasuringPoint, MeasuringPointImage
from . import serializers


class MeasuringPointViewMixin(ProjectMembershipRequiredMixin):
    def get_related_project(self, obj: MeasuringPoint | None = None) -> Project | None:
        if obj:
            return obj.run.project
        return get_object_or_404(Run, id=self.kwargs["run_id"]).project

    def get_queryset(self):
        run_id = self.kwargs["run_id"]
        return MeasuringPoint.objects.filter(run_id=run_id).order_by("created")


class MeasuringPointsView(
    MeasuringPointViewMixin, generics.ListCreateAPIView
):  # pylint: disable=too-many-ancestors
    serializer_class = serializers.MeasuringPointsSerializer

    def perform_create(self, serializer):
        serializer.save(run_id=self.kwargs["run_id"])

    def get_queryset(self):
        return super().get_queryset().select_related("image")


class MeasuringPointView(MeasuringPointViewMixin, generics.UpdateAPIView):
    serializer_class = serializers.MeasuringPointsSerializer

    def get_queryset(self):
        run_id = self.kwargs["run_id"]
        return MeasuringPoint.objects.filter(run_id=run_id)


class MeasuringPointImageCreateView(  # pylint: disable=too-many-ancestors
    ProjectMembershipRequiredMixin,
    generics.CreateAPIView,
    generics.UpdateAPIView,
    generics.DestroyAPIView,
):
    serializer_class = serializers.MeasuringPointImageSerializer

    def get_related_project(
        self, obj: MeasuringPointImage | None = None
    ) -> Project | None:
        if not obj:
            point_id = self.kwargs["measuring_point_id"]
            # pylint: disable=protected-access
            return get_object_or_404(
                MeasuringPoint._base_manager, id=point_id
            ).run.project
        return obj.measuring_point.run.project if obj else None

    def get_queryset(self):
        return MeasuringPointImage.objects.filter(
            measuring_point_id=self.kwargs["measuring_point_id"]
        )

    def perform_create(self, serializer):
        serializer.save(measuring_point_id=self.kwargs["measuring_point_id"])

    def get_object(self):
        obj = get_object_or_404(self.get_queryset())
        self.check_object_permissions(self.request, obj)
        return obj
