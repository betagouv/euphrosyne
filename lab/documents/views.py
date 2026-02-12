import json
from typing import Any, Dict

from django.contrib.admin import site
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from lab.permissions import ProjectMembershipRequiredMixin
from lab.project_immutability import is_project_data_immutable

from ..models import Project


class ProjectDocumentsView(ProjectMembershipRequiredMixin, TemplateView):
    template_name = "documents/project_documents.html"
    project: Project

    # pylint: disable=arguments-differ
    def dispatch(
        self, request: HttpRequest, project_id: int, *args, **kwargs
    ) -> HttpResponse:
        self.project = get_object_or_404(Project, pk=project_id)
        return super().dispatch(request, project_id, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        can_write = not is_project_data_immutable(self.project)

        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "subtitle": self.project.name + " | " + _("Upload documents"),
            "project": self.project,
            "json_data": json.dumps(
                {
                    "project": {
                        "name": self.project.name,
                        "slug": self.project.slug,
                    },
                    "table": {"canDelete": can_write},
                    "form": {
                        "canUpload": can_write,
                        "hintText": gettext(
                            "Multiple files allowed. "
                            "Allowed files: images, documents and archives."
                        ),
                    },
                }
            ),
        }
