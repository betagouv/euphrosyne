from typing import Any, List, Mapping, Optional, Type

from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.forms.models import ModelForm, inlineformset_factory
from django.http.request import HttpRequest

from shared.admin import ModelAdmin

from ..forms import BaseParticipationForm, LeaderParticipationForm
from ..lib import is_lab_admin
from ..models import Participation, Project


class ParticipationInline(admin.TabularInline):
    model = Participation

    def get_formset(
        self,
        request: HttpRequest,
        obj: Optional[Project] = ...,
        **kwargs: Mapping[str, Any]
    ):
        form = BaseParticipationForm if obj else LeaderParticipationForm
        formset = inlineformset_factory(
            Project,
            Participation,
            form=form,
            extra=0,
            min_num=1,
            # On creation, only leader participation can be added
            max_num=1000 if obj else 1,
            can_delete=bool(obj),
        )
        return formset


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:project member
@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ("name", "leader")
    readonly_fields = ("members", "leader")

    def has_view_permission(self, request: HttpRequest, obj: Optional[Project] = None):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.participation_set.filter(user_id=request.user.id).exists()
        ) and super().has_view_permission(request, obj)

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Project] = None
    ):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.members.filter(id=request.user.id).exists()
        ) and super().has_change_permission(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Project] = None
    ):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.leader.user_id == request.user.id
        ) and super().has_delete_permission(request, obj)

    def get_exclude(self, request: HttpRequest, obj: Optional[Project] = None):
        excluded = super().get_exclude(request, obj)
        if not is_lab_admin(request.user):
            return excluded + ("project",) if excluded else ("project",)
        return excluded

    def get_readonly_fields(self, request: HttpRequest, obj: Optional[Project] = None):
        """Set edit permission based on user role."""
        # Admin
        readonly_fields = super().get_readonly_fields(request, obj)
        if not is_lab_admin(request.user):
            if obj and obj.leader.user_id != request.user.id:
                # Participant on change
                readonly_fields = readonly_fields + ("name",)
        return readonly_fields

    def get_queryset(self, request: HttpRequest):
        projects_qs = super().get_queryset(request)
        if is_lab_admin(request.user):
            return projects_qs
        return projects_qs.filter(participation__user_id=request.user.id).distinct()

    def get_inlines(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> List[Type[InlineModelAdmin]]:
        inlines = super().get_inlines(request, obj=obj)
        if is_lab_admin(request.user) or (
            obj and obj.leader.user_id == request.user.id
        ):
            return inlines + [ParticipationInline]
        return inlines

    def save_model(
        self,
        request: HttpRequest,
        obj: Project,
        form: ModelForm,
        change: bool,
    ) -> None:
        obj.save()
        if not change and not is_lab_admin(request.user):
            obj.participation_set.create(user_id=request.user.id, is_leader=True)
