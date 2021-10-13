from typing import Optional, Union

from django.contrib import admin
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from .forms import ProjectForm, ProjectFormForNonAdmins
from .lib import is_lab_admin
from .models import Participation, Project, Run


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:project member
@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ("label", "date", "project")

    def has_view_permission(self, request: HttpRequest, obj: Optional[Run] = None):
        """Allow list view but only allow detail to leader or admin"""
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
            or obj.project.members.filter(id=request.user.id).exists()
        ) and super().has_view_permission(request, obj)

    def has_change_permission(self, request: HttpRequest, obj: Optional[Run] = None):
        """Allow change in general but only allow specific edition to leader or admin"""
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
        ) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Run] = None):
        """Allow deletion in general but only allow specific del to leader or admin"""
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
        ) and super().has_delete_permission(request, obj)

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

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self, db_field, request: HttpRequest, queryset: QuerySet[Run] = None, **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "project":
            queryset = Project.objects.filter(leader=request.user)

        return super().formfield_for_foreignkey(
            db_field, request, queryset=queryset, **kwargs
        )


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


# [XXX] Add Tests
# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:<custom (obj.user)>
@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ("project", "user")
    readonly_fields = ("project", "user")

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[Participation] = None
    ):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
            or obj.user == request.user
        ) and super().has_view_permission(request, obj)

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Participation] = None
    ):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
            or obj.user == request.user
        ) and super().has_change_permission(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Participation] = None
    ):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.project.leader_id == request.user.id
            or obj.user == request.user
        ) and super().has_delete_permission(request, obj)

    def get_queryset(self, request: HttpRequest):
        """
        Non admins are only allowed to see their own participations or
        participations of projects that they lead.
        """
        runs_queryset = super().get_queryset(request)
        if is_lab_admin(request.user):
            return runs_queryset
        return runs_queryset.filter(
            Q(project__leader=request.user) | Q(user=request.user)
        )

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self,
        db_field,
        request: HttpRequest,
        queryset: QuerySet[Participation] = None,
        **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "project":
            queryset = Project.objects.filter(leader=request.user)

        return super().formfield_for_foreignkey(
            db_field, request, queryset=queryset, **kwargs
        )
