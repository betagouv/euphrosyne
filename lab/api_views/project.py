from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, IsAdminUser

from lab.permissions import is_lab_admin, is_project_leader
from lab.runs.models import Run

from ..models import Participation, Project
from .participation import (
    LeaderParticipationCreateUpdateView,
    MemberParticipationListCreateGroupView,
    MemberParticipationRetrieveUpdateDestroyGroupView,
)
from .permissions import IsLabAdminUser, IsLeaderOrReadOnlyMixin
from .serializers import (
    OnPremisesParticipationSerializer,
    ProjectSerializer,
    UpcomingProjectSerializer,
)


class ProjectFilter(filters.FilterSet):
    start_before = filters.DateFilter(field_name="start_date", method="filter_before")
    start_after = filters.DateFilter(field_name="end_date", method="filter_after")
    end_before = filters.DateFilter(field_name="start_date", method="filter_before")
    end_after = filters.DateFilter(field_name="end_date", method="filter_after")

    class Meta:
        model = Project
        fields = ["start_before", "start_after", "end_before", "end_after"]

    def filter_before(self, queryset, name, value):
        # Ensure value is timezone-aware
        if hasattr(value, "tzinfo") and value.tzinfo is None:
            value = timezone.make_aware(value)
        lookup = f"runs__{name}__lte"
        return queryset.filter(**{lookup: value}).distinct()

    def filter_after(self, queryset, name, value):
        # Ensure value is timezone-aware
        if hasattr(value, "tzinfo") and value.tzinfo is None:
            value = timezone.make_aware(value)
        lookup = f"runs__{name}__gte"
        return queryset.filter(**{lookup: value}).distinct()


class ProjectList(generics.ListAPIView):
    """List projects with optional filters on start and end dates in the query params.
    Filters names: start_before, start_after, end_before, end_after.
    Example: <URL>?start_after=2023-06-30&end_before=2023-07-23"""

    queryset = (
        Project.objects.order_by("name")
        .prefetch_related("runs__run_object_groups")
        .all()
    )
    serializer_class = ProjectSerializer
    permission_classes = [IsLabAdminUser]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ProjectFilter


class UpcomingProjectList(generics.ListAPIView):
    runs = Run.objects.filter(start_date__gte=timezone.now()).distinct("project")[:5]
    queryset = (
        Project.objects.filter(runs__in=runs)
        .distinct()
        .order_by("runs__start_date")[:4]
    )
    serializer_class = UpcomingProjectSerializer
    permission_classes = [IsLabAdminUser]


class ProjectParticipationListCreateGroupView(MemberParticipationListCreateGroupView):
    permission_classes = [IsLeaderOrReadOnlyMixin]

    def get_related_project(self, obj: Participation | None = None) -> Project | None:
        if obj:
            return obj.project
        project_id = self.kwargs.get("project_id")
        return Project.objects.filter(id=project_id).first()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                project=self.get_related_project(),
                is_leader=False,
            )
        )

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "project": self.get_related_project(),
        }


class ProjectOnPremisesParticipationListCreateGroupView(
    ProjectParticipationListCreateGroupView
):
    serializer_class = OnPremisesParticipationSerializer

    def perform_create(self, serializer: serializers.ModelSerializer):
        serializer.save(on_premises=True, project=self.get_related_project())

    def get_queryset(self):
        return super().get_queryset().filter(on_premises=True)


class ProjectRemoteParticipationListCreateGroupView(
    ProjectParticipationListCreateGroupView
):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(on_premises=False, project=self.get_related_project())
        )

    def perform_create(self, serializer: serializers.ModelSerializer):
        serializer.save(on_premises=False, project=self.get_related_project())


# pylint: disable=too-many-ancestors
class ProjectParticipationRetrieveUpdateDestroyGroupView(
    IsLeaderOrReadOnlyMixin, MemberParticipationRetrieveUpdateDestroyGroupView
):
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                project=self.get_related_project(),
                is_leader=False,
            )
        )

    def get_related_project(self, obj=None) -> Project | None:
        if obj:
            return obj.project
        project_id = self.kwargs.get("project_id")
        return Project.objects.filter(id=project_id).first()


class ProjectLeaderParticipationRetrieveCreateUpdateGroupView(
    LeaderParticipationCreateUpdateView
):
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                project=self.get_related_project(),
                is_leader=True,
            )
        )

    def get_related_project(self, obj=None) -> Project | None:
        if obj:
            return obj.project
        project_id = self.kwargs.get("project_id")
        return Project.objects.filter(id=project_id).first()

    def check_permissions(self, request):
        """Allow project members to read, and only lab admins/leaders to update.

        Lab admins retain full management access, including creating a leader
        participation and changing the leader user. Project leaders may only
        update their own leader participation. Other project members may read
        the leader participation but cannot modify it.
        """
        super().check_permissions(request)
        project = self.get_related_project()
        if project is None:
            return
        if is_lab_admin(request.user):
            return
        if request.method in SAFE_METHODS:
            if project.participation_set.filter(user=request.user).exists():
                return
        elif request.method in ("PATCH", "PUT"):
            if is_project_leader(request.user, project):
                return
        raise PermissionDenied()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "project": self.get_related_project(),
        }

    def get_serializer(self, *args, **kwargs):
        if (
            getattr(self, "request", None)
            and not is_lab_admin(self.request.user)
            and self.request.method in ("PATCH", "PUT")
            and "data" in kwargs
        ):
            data = kwargs["data"].copy()
            data.pop("user", None)
            kwargs["data"] = data
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer: serializers.ModelSerializer):
        serializer.save(
            on_premises=True, project=self.get_related_project(), is_leader=True
        )

    def perform_update(self, serializer: serializers.ModelSerializer):
        serializer.save(is_leader=True)
