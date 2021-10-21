from typing import Optional

from django.contrib import admin
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from shared.admin import ModelAdmin

from ..lib import is_lab_admin
from ..models import Participation, Project


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:<custom (obj.user)>
@admin.register(Participation)
class ParticipationAdmin(ModelAdmin):
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
