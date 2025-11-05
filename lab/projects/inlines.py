from django.contrib import admin
from django.http.request import HttpRequest

from lab.admin.mixins import LabPermission, LabPermissionMixin, LabRole

from .forms import (
    BeamTimeRequestForm,
)
from .models import BeamTimeRequest, Project


class BeamTimeRequestInline(LabPermissionMixin, admin.StackedInline):
    model = BeamTimeRequest
    form = BeamTimeRequestForm
    fields = ("request_type", "request_id", "form_type", "problem_statement")

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(  # type: ignore[override]
        self,
        obj: Project | None = None,
    ) -> Project | None:
        return obj

    def has_delete_permission(
        self, request: HttpRequest, obj: Project | None = None  # type: ignore[override]
    ) -> bool:
        # should only add or edit
        return False
