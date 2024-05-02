import json
from typing import Any

from django.contrib.admin import site
from django.contrib.admin.options import IS_POPUP_VAR
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from lab.models import Participation
from lab.permissions import is_lab_admin
from shared.view_mixins import StaffUserRequiredMixin

from .forms import ChangeLeaderForm
from .models import Project


class ChangeLeaderView(StaffUserRequiredMixin, FormView):
    template_name = "admin/change_leader.html"
    form_class = ChangeLeaderForm

    project: Project

    # pylint: disable=arguments-differ
    def dispatch(self, request: HttpRequest, project_id: int, *args, **kwargs):
        if not is_lab_admin(request.user):
            raise PermissionDenied()
        return self._process_request(request, project_id, *args, **kwargs)

    def _process_request(self, request, project_id, *args, **kwargs):
        with transaction.atomic():
            self.project = get_object_or_404(Project, pk=project_id)
            return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _update_participation(
        project: Project, leader_participation_id: int
    ) -> QuerySet[Participation]:
        project.participation_set.filter(is_leader=True).update(is_leader=False)
        new_leader_participation_id = leader_participation_id
        participation_qs = project.participation_set.filter(
            id=new_leader_participation_id
        )
        participation_qs.update(is_leader=True)
        return participation_qs

    def form_valid(self, form):
        leader_participation_id = form.cleaned_data["leader_participation"].id
        participation_qs = self._update_participation(
            self.project, leader_participation_id
        )

        if IS_POPUP_VAR in self.request.POST:
            obj = participation_qs.get().user
            value = obj.serializable_value(obj._meta.pk.attname)
            popup_response_data = json.dumps(
                {
                    "action": "change",
                    "obj": str(obj),
                    "new_value": str(value),
                }
            )
            return TemplateResponse(
                self.request,
                "admin/view_popup_response.html",
                {
                    "popup_response_data": popup_response_data,
                },
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("admin:lab_project_change", args=[self.project.id])

    def get_form_kwargs(self) -> dict[str, Any]:
        return {**super().get_form_kwargs(), "project": self.project}

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "subtitle": self.project.name + " | " + _("Change leader"),
            "project": self.project,
            "is_popup": IS_POPUP_VAR in self.request.GET,
            "is_popup_var": IS_POPUP_VAR,
        }
