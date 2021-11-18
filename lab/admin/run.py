from typing import Optional

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from ..lib import is_lab_admin
from ..models import Project, Run
from .mixins import LabPermission, LabPermissionMixin, LabRole


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:project member
@admin.register(Run)
class RunAdmin(LabPermissionMixin, ModelAdmin):
    list_display = ("label", "date", "project")

    lab_permissions = LabPermission(
        add_permission=LabRole.ANY_USER,
        view_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_LEADER,
        delete_permission=LabRole.PROJECT_LEADER,
    )

    def get_related_project(self, obj: Optional[Run] = None) -> Optional[Project]:
        if obj:
            return obj.project
        return None

    # This one seems redundant with `get_readonly_fields` according to the
    # `ModelAdmin` view:
    def get_exclude(self, request: HttpRequest, obj: Optional[Run] = None):
        excluded = super().get_exclude(request, obj)
        if obj:
            return excluded + ("project",) if excluded else ("project",)
        return excluded

    def get_readonly_fields(self, request: HttpRequest, obj: Optional[Run] = None):
        """Don't allow changing project in change mode"""
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            return readonly_fields + ("project",)
        return readonly_fields

    def get_queryset(self, request: HttpRequest):
        runs_queryset = super().get_queryset(request)
        if is_lab_admin(request.user):
            return runs_queryset
        return runs_queryset.filter(project__members__id=request.user.id)

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self, db_field, request: HttpRequest, queryset: QuerySet[Run] = None, **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "project":
            queryset = Project.objects.filter(
                participation__user_id=request.user.id,
                participation__is_leader=True,
            )

        return super().formfield_for_foreignkey(
            db_field, request, queryset=queryset, **kwargs
        )
