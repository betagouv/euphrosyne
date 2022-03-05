from typing import Any, Dict

from django.contrib.admin import site
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from shared.view_mixins import StaffUserRequiredMixin

from ..models import Project
from ..permissions import is_lab_admin


class ProjectDocumentsView(StaffUserRequiredMixin, TemplateView):
    template_name = "admin/project_documents.html"
    project: Project

    # pylint: disable=arguments-differ
    def dispatch(
        self, request: HttpRequest, project_id: int, *args, **kwargs
    ) -> HttpResponse:
        self.project = get_object_or_404(Project, pk=project_id)
        response = super().dispatch(request, *args, **kwargs)
        if (
            not is_lab_admin(request.user)
            and not self.project.members.filter(id=request.user.id).exists()
        ):
            return self.handle_no_permission()
        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "subtitle": self.project.name + " | " + _("Upload documents"),
            "project": self.project,
        }
