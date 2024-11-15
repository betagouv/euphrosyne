from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from lab.api_views.permissions import ProjectMembershipRequiredMixin
from lab.measuring_points.models import MeasuringPoint
from lab.projects.models import Project

from . import serializers
from .. import models


class StandardListView(generics.ListAPIView):
    serializer_class = serializers.StandardSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return models.Standard.objects.all()


class MeasuringPointStandardView(
    ProjectMembershipRequiredMixin,
    generics.RetrieveAPIView,
    generics.CreateAPIView,
    generics.UpdateAPIView,
    generics.DestroyAPIView,
):
    serializer_class = serializers.MeasuringPointStandardSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return models.MeasuringPointStandard.objects.all()

    def get_related_project(
        self, obj: models.MeasuringPointStandard | None = None
    ) -> Project | None:
        if not obj:
            point_id = self.kwargs["measuring_point_id"]
            # pylint: disable=protected-access
            return MeasuringPoint._base_manager.get(id=point_id).run.project
        return obj.measuring_point.run.project if obj else None

    def perform_create(self, serializer):
        serializer.save(
            measuring_point_id=self.kwargs["measuring_point_id"],
            standard=models.Standard.objects.get(
                label=serializer.validated_data["standard"]["label"]
            ),
        )

    def perform_update(self, serializer):
        standard = models.Standard.objects.get(
            label=serializer.validated_data["standard"]["label"]
        )
        serializer.instance.standard = standard
        serializer.instance.save()

    def get_object(self):
        point_id = self.kwargs["measuring_point_id"]
        try:
            obj = models.MeasuringPointStandard.objects.get(measuring_point_id=point_id)
            self.check_object_permissions(self.request, obj)
            return obj
        except models.MeasuringPointStandard.DoesNotExist:
            raise NotFound(
                detail="No standard linked to this measuring point",
            )
