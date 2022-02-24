from typing import Any, Dict

from django.contrib.admin import site
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ..models import Project
from ..permissions import ProjectMembershipRequiredMixin, is_lab_admin


class WorkplaceView(ProjectMembershipRequiredMixin, TemplateView):
    template_name = "workplace/workplace.html"
    project: Project

    # pylint: disable=arguments-differ
    def dispatch(
        self, request: HttpRequest, project_id: int, *args, **kwargs
    ) -> HttpResponse:
        self.project = get_object_or_404(Project, pk=project_id)
        return super().dispatch(request, project_id, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        runs = tuple(
            {
                "id": id,
                "label": label,
                "raw_data_table": {
                    "attrs": {"id": f"run-{id}-raw-data-table"},
                    "can_delete": is_lab_admin(self.request.user),
                },
                "processed_data_table": {
                    "attrs": {"id": f"run-{id}-processed-data-table"},
                    "can_delete": is_lab_admin(self.request.user),
                },
                "raw_data_upload_form": {
                    "attrs": {
                        "id": f"run-{id}-raw-data-upload-form",
                        "project-id": self.project.id,
                    }
                },
                "processed_data_upload_form": {
                    "attrs": {
                        "id": f"run-{id}-processed-data-upload-form",
                        "project-id": self.project.id,
                    }
                },
            }
            for (id, label) in self.project.runs.values_list("id", "label")
        )
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "project": self.project,
            "subtitle": "{} | {}".format(self.project.name, _("Workplace")),
            "runs": runs,
        }
