from django.shortcuts import get_object_or_404
from rest_framework import generics

from lab.api_views.permissions import ProjectMembershipRequiredMixin
from lab.projects.models import Project

from ...models import RunNotebook
from . import serializers


class RunNotebookView(ProjectMembershipRequiredMixin, generics.UpdateAPIView):
    queryset = RunNotebook.objects.all()
    serializer_class = serializers.RunNotebookSerializer

    lookup_url_kwarg = "run_id"

    def get_related_project(self, obj: RunNotebook | None = None) -> Project | None:
        if not obj:
            return None
        return obj and obj.run.project

    def get_object(self):
        """Same as generics.GenericAPIView.get_object
        but use run_id instead."""
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {"run_id": self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
