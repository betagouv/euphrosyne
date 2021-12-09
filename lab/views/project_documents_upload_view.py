from typing import Any, Dict

from django import forms
from django.contrib.admin import site
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

from ..models import Project
from ..object_storage import upload_project_document


class ProjectDocumentsUploadForm(forms.Form):
    documents = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True})
    )


class ProjectDocumentsUploadView(LoginRequiredMixin, FormView):
    form_class = ProjectDocumentsUploadForm
    template_name = "admin/project_documents_upload.html"

    def dispatch(self, request: HttpRequest, project_id: int, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        # pylint: disable=attribute-defined-outside-init
        self.project = get_object_or_404(Project, pk=project_id)
        if not self.project.members.filter(id=request.user.id).exists():
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist("documents")
        if form.is_valid():
            for file in files:
                print(file)
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "project": self.project,
        }
