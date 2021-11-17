from typing import Optional

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.http.request import HttpRequest

from lab.admin.mixins import LabAdminAllowedMixin
from lab.lib import is_lab_admin

from ..models import BeamTimeRequest

ADMIN_FIELDS = (
    "project",
    "request_type",
    "request_id",
    "problem_statement",
    "form_type",
)


# Allowance: ADMIN:lab admin
@admin.register(BeamTimeRequest)
class BeamTimeRequestAdmin(LabAdminAllowedMixin, ModelAdmin):
    list_display = ("project", "request_type")
    fields = ADMIN_FIELDS
    readonly_fields = ADMIN_FIELDS

    def get_queryset(self, request: HttpRequest):
        projects_qs = super().get_queryset(request)
        if is_lab_admin(request.user):
            return projects_qs
        return projects_qs.filter(
            project__participation__user_id=request.user.id
        ).distinct()

    # pylint: disable=no-self-use
    def has_add_permission(
        self, request: HttpRequest, obj: Optional[BeamTimeRequest] = None
    ) -> bool:
        # User should only create beam time requests
        # via the inline form present in the Project admin page
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[BeamTimeRequest] = None
    ) -> bool:
        return False
