from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import generics

from lab.runs.models import Run

from ..models import Project
from .permissions import IsLabAdminUser
from .serializers import ProjectSerializer, UpcomingProjectSerializer


class ProjectFilter(filters.FilterSet):
    start_before = filters.DateFilter(field_name="start_date", method="filter_before")
    start_after = filters.DateFilter(field_name="end_date", method="filter_after")
    end_before = filters.DateFilter(field_name="start_date", method="filter_before")
    end_after = filters.DateFilter(field_name="end_date", method="filter_after")

    class Meta:
        model = Project
        fields = ["start_before", "start_after", "end_before", "end_after"]

    def filter_before(self, queryset, name, value):
        lookup = f"runs__{name}__lte"
        return queryset.filter(**{lookup: value}).distinct()

    def filter_after(self, queryset, name, value):
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
