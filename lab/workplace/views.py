import json
from typing import Any, Dict

from django.apps import apps
from django.contrib.admin import site
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from lab.project_immutability import is_project_data_immutable

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
        user_is_lab_admin = is_lab_admin(self.request.user)
        can_write = user_is_lab_admin and not is_project_data_immutable(self.project)
        can_start_vm = not is_project_data_immutable(self.project)

        runs = tuple(
            {
                "id": id,
                "label": label,
            }
            for (id, label) in self.project.runs.values_list("id", "label")
        )
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "project": self.project,
            "subtitle": "{} | {}".format(self.project.name, _("Workplace")),
            "runs": runs,
            "can_start_vm": can_start_vm,
            "json_data": json.dumps(
                {
                    "project": {
                        "name": self.project.name,
                        "slug": self.project.slug,
                        "id": self.project.id,
                    },
                    "isLabAdmin": user_is_lab_admin,
                    "isDataManagementEnabled": apps.is_installed("data_management"),
                    "labels": {
                        "dataManagementTitle": str(_("Data management")),
                        "loading": str(_("Loading")),
                    },
                    "runs": [
                        {
                            "id": run["id"],
                            "label": run["label"],
                            "rawDataTable": {
                                "canDelete": can_write,
                            },
                            "processedDataTable": {
                                "canDelete": can_write,
                            },
                        }
                        for run in runs
                    ],
                }
            ),
        }
