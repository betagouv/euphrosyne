from typing import Any, Dict

from django.contrib.admin import site
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.edit import FormView

from ..forms import ChangeLeaderForm
from ..permissions import is_lab_admin
from ..models import Project


class ChangeLeaderView(LoginRequiredMixin, FormView):
    template_name = "admin/change_leader.html"
    form_class = ChangeLeaderForm

    # pylint: disable=arguments-differ
    def dispatch(self, request: HttpRequest, project_id: int, *args, **kwargs):
        if not is_lab_admin(request.user):
            raise PermissionDenied()
        # pylint: disable=attribute-defined-outside-init
        self.project = get_object_or_404(Project, pk=project_id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            self.project.participation_set.filter(is_leader=True).update(
                is_leader=False
            )
            new_leader_participation = form.cleaned_data["leader_participation"].id
            self.project.participation_set.filter(id=new_leader_participation).update(
                is_leader=True
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("admin:lab_project_change", args=[self.project.id])

    def get_form_kwargs(self) -> Dict[str, Any]:
        return {**super().get_form_kwargs(), "project": self.project}

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "project": self.project,
        }
