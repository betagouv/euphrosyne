from typing import Optional

from django.contrib import admin
from django.db.models import Q
from django.http.request import HttpRequest

from shared.admin import ModelAdmin

from ..lib import is_lab_admin
from ..models import Run


# Allowance: ADMIN:lab admin, EDITOR:lab admin, VIEWER:project member
@admin.register(Run)
class RunAdmin(ModelAdmin):
    list_display = ("label", "date", "project")

    def has_view_permission(self, request: HttpRequest, obj: Optional[Run] = None):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
            or obj.project.members.filter(id=request.user.id).exists()
        ) and super().has_view_permission(request, obj)

    def has_add_permission(self, request: HttpRequest):
        return is_lab_admin(request.user) and super().has_add_permission(request)

    def has_change_permission(self, request: HttpRequest, obj: Optional[Run] = None):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
        ) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Run] = None):
        return is_lab_admin(request.user) and super().has_delete_permission(
            request, obj
        )

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
        return runs_queryset.filter(
            Q(project__leader=request.user) | Q(project__members__id=request.user.id)
        )
