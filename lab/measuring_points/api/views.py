from rest_framework import generics

from ...api_views.permissions import ProjectMembershipRequiredMixin
from ...projects.models import Project
from ..models import MeasuringPoint, MeasuringPointImage
from . import serializers


class MeasuringPointViewMixin(ProjectMembershipRequiredMixin):
    def get_related_project(self, obj: MeasuringPoint | None = None) -> Project | None:
        return obj.run.project if obj else None

    def get_queryset(self):
        run_id = self.kwargs["run_id"]
        return MeasuringPoint.objects.filter(run_id=run_id).order_by("created")


class MeasuringPointsView(
    MeasuringPointViewMixin, generics.ListCreateAPIView
):  # pylint: disable=too-many-ancestors
    serializer_class = serializers.MeasuringPointsSerializer

    def perform_create(self, serializer):
        serializer.save(run_id=self.kwargs["run_id"])


class MeasuringPointView(MeasuringPointViewMixin, generics.UpdateAPIView):
    serializer_class = serializers.MeasuringPointsSerializer

    def get_related_project(self, obj: MeasuringPoint | None = None) -> Project | None:
        if not obj:
            return None
        return obj.run.project if obj else None

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
            return MeasuringPoint._base_manager.get(id=point_id).run.project
        return obj.measuring_point.run.project if obj else None

    def get_queryset(self):
        return MeasuringPointImage.objects.filter(
            measuring_point_id=self.kwargs["measuring_point_id"]
        )

    def perform_create(self, serializer):
        serializer.save(measuring_point_id=self.kwargs["measuring_point_id"])

    def get_object(self):
        point_id = self.kwargs["measuring_point_id"]
        return MeasuringPoint.objects.get(id=point_id).image
