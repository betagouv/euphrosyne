from typing import Optional, Union

from django.contrib import admin
from django.db.models import Q
from django.http.request import HttpRequest

from ..forms import ProjectForm, ProjectFormForNonAdmins
from ..lib import is_lab_admin
from ..models import Project


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:project member
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "leader")
    readonly_fields = ("members",)

    def has_view_permission(self, request: HttpRequest, obj: Optional[Project] = None):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.leader_id == request.user.id
            or obj.members.filter(id=request.user.id).exists()
        ) and super().has_view_permission(request, obj)

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Project] = None
    ):
        return (
            is_lab_admin(request.user) or not obj or obj.leader_id == request.user.id
        ) and super().has_change_permission(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Project] = None
    ):
        return (
            is_lab_admin(request.user) or not obj or obj.leader_id == request.user.id
        ) and super().has_delete_permission(request, obj)

    def get_exclude(self, request: HttpRequest, obj: Optional[Project] = None):
        excluded = super().get_exclude(request, obj)
        if not is_lab_admin(request.user):
            return excluded + ("project",) if excluded else ("project",)
        return excluded

    def get_readonly_fields(self, request: HttpRequest, obj: Optional[Project] = None):
        """Allow only to admins to change leader"""
        readonly_fields = super().get_readonly_fields(request, obj)
        if not is_lab_admin(request.user):
            return readonly_fields + ("leader",)
        return readonly_fields

    def get_queryset(self, request: HttpRequest):
        projects_qs = super().get_queryset(request)
        if is_lab_admin(request.user):
            return projects_qs
        return projects_qs.filter(
            Q(leader=request.user) | Q(members__id=request.user.id)
        )

    def save_model(
        self,
        request: HttpRequest,
        obj: Project,
        form: Union[ProjectFormForNonAdmins, ProjectForm],
        change: bool,
    ) -> None:
        if not is_lab_admin(request.user):
            obj.leader_id = request.user.id
        obj.save()
        obj.members.add(obj.leader_id)
