import json
from typing import Any, Dict

from django.contrib.admin import site
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ..models import Project
from ..permissions import ProjectMembershipRequiredMixin, is_lab_admin
from data_management.models import LifecycleState, ProjectData


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
        project_data = ProjectData.for_project(self.project)
        user_is_lab_admin = is_lab_admin(self.request.user)
        can_delete_files = (
            user_is_lab_admin and project_data.lifecycle_state == LifecycleState.HOT
        )
        can_delete_files_when_hot = user_is_lab_admin
        last_lifecycle_operation = project_data.last_lifecycle_operation
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
            "json_data": json.dumps(
                {
                    "project": {
                        "name": self.project.name,
                        "slug": self.project.slug,
                        "id": self.project.id,
                        "lifecycleState": project_data.lifecycle_state,
                        "lastLifecycleOperationId": (
                            str(last_lifecycle_operation.operation_id)
                            if last_lifecycle_operation
                            else None
                        ),
                        "lastLifecycleOperationType": (
                            last_lifecycle_operation.type
                            if last_lifecycle_operation
                            else None
                        ),
                    },
                    "isLabAdmin": user_is_lab_admin,
                    "runs": [
                        {
                            "id": run["id"],
                            "label": run["label"],
                            "rawDataTable": {
                                "canDelete": can_delete_files,
                                "canDeleteWhenHot": can_delete_files_when_hot,
                            },
                            "processedDataTable": {
                                "canDelete": can_delete_files,
                                "canDeleteWhenHot": can_delete_files_when_hot,
                            },
                        }
                        for run in runs
                    ],
                }
            ),
        }
