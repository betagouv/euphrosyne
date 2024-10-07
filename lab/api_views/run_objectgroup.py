from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from .. import models
from ..permissions import is_lab_admin
from . import serializers


class RunObjectGroupMixin:
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = models.Run.run_object_groups.through.objects
        if not is_lab_admin(self.request.user):
            user_projects = models.Project.objects.filter(
                members__id=self.request.user.id
            )
            return qs.filter(run__project__in=user_projects).distinct()
        return qs


class RunObjectGroupView(
    RunObjectGroupMixin, generics.ListAPIView, generics.CreateAPIView
):
    lookup_field = "run_id"

    def get_serializer_class(self):
        if self.request.method == "POST":
            # create
            return serializers.RunObjectGroupCreateSerializer
        # list
        return serializers.RunObjectGroupSerializer

    def get_queryset(self):
        filter_params = {self.lookup_field: self.kwargs[self.lookup_field]}
        return super().get_queryset().filter(**filter_params)

    def perform_create(self, serializer):
        run_id = self.kwargs[self.lookup_field]
        if (
            not is_lab_admin(self.request.user)
            and not models.Project.objects.filter(
                members__id=self.request.user.id,
                runs__id=run_id,
            ).exists()
        ):
            raise PermissionDenied("You don't have access to this project")
        serializer.validated_data["run_id"] = run_id
        super().perform_create(serializer)


class RunObjectGroupDeleteView(RunObjectGroupMixin, generics.DestroyAPIView):
    pass


class RunObjectGroupAvailableListView(RunObjectGroupMixin, generics.ListAPIView):
    """List all object groups available for a run (in other words,
    those that are part of any run within the same project)."""

    serializer_class = serializers.AvailableObjectGroupSerializer
    lookup_field = "run_id"

    def get_queryset(self):
        run_qs = models.Run.objects.filter(id=self.kwargs[self.lookup_field])
        if not is_lab_admin(self.request.user):
            run_qs = run_qs.filter(project__members__id=self.request.user.id)
        run = run_qs.first()
        if not run:
            raise Http404()
        run_object_groups = models.Run.run_object_groups.through.objects.filter(
            run_id=self.kwargs[self.lookup_field]
        )
        return (
            models.ObjectGroup.objects.filter(
                runs__in=models.Run.objects.filter(project=run.project)
            )
            .exclude(id__in=run_object_groups.values_list("objectgroup_id", flat=True))
            .distinct()
        )


class RunObjectGroupImagesView(generics.ListCreateAPIView):
    serializer_class = serializers.RunObjectGroupImageSerializer

    def get_queryset(self):
        run_object_group_id = self.kwargs["run_object_group_id"]
        return models.RunObjetGroupImage.objects.filter(
            run_object_group_id=run_object_group_id
        )

    def perform_create(self, serializer):
        serializer.save(run_object_group_id=self.kwargs["run_object_group_id"])
