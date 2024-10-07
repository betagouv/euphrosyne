import json
from typing import Any, Dict

from django.contrib.admin import site
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from lab import models as lab_models
from lab.permissions import ProjectMembershipRequiredMixin


class NotebookView(ProjectMembershipRequiredMixin, TemplateView):
    template_name = "notebook/notebook.html"
    run: lab_models.Run

    # pylint: disable=arguments-differ
    def dispatch(
        self, request: HttpRequest, run_id: int, *args, **kwargs
    ) -> HttpResponse:
        self.run = get_object_or_404(lab_models.Run, pk=run_id)
        return super().dispatch(request, self.run.project_id, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "title": _("Notebook: %s") % self.run.label,
            "run": self.run,
            "project": self.run.project,
            "notebook": self.run.run_notebook,
            "json_data": json.dumps(
                {"runId": str(self.run.id), "projectSlug": self.run.project.slug}
            ),
        }
