from typing import Any, List, Mapping, Optional, Tuple, Type, Union

from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.forms.widgets import Select
from django.http.request import HttpRequest
from django.urls import reverse

from euphro_auth.models import User
from shared.admin import ModelAdmin

from ..forms import (
    ParticipationWithEmailInvitForm,
    ProjectForm,
    ProjectFormForNonAdmins,
)
from ..lib import is_lab_admin
from ..models import Participation, Project


class UserWidgetWrapper(RelatedFieldWidgetWrapper):
    def get_related_url(self, info: Tuple[str, str], action: str, *args: Any) -> str:
        if action == "add":
            return reverse("admin:euphro_auth_userinvitation_add")
        return super().get_related_url(info, action, *args)


class ParticipationInline(admin.TabularInline):
    model = Participation

    def get_formset(
        self,
        request: HttpRequest,
        obj: Optional[Project] = ...,
        **kwargs: Mapping[str, Any]
    ):
        formset = inlineformset_factory(
            Project,
            Participation,
            fields=("user",),
            widgets={
                "user": UserWidgetWrapper(
                    Select(),
                    User.participation_set.rel,
                    self.admin_site,
                )
            },
            form=ParticipationWithEmailInvitForm,
        )
        return formset


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:project member
@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ("name", "leader")
    readonly_fields = ("members",)

    def has_view_permission(self, request: HttpRequest, obj: Optional[Project] = None):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.leader_id == request.user.id
            or obj.participation_set.filter(user_id=request.user.id).exists()
        ) and super().has_view_permission(request, obj)

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Project] = None
    ):
        return (
            is_lab_admin(request.user)
            or not obj
            or obj.leader_id == request.user.id
            or obj.members.filter(id=request.user.id).exists()
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
        """Set edit permission based on user role."""
        # Admin
        readonly_fields = super().get_readonly_fields(request, obj)
        if not is_lab_admin(request.user):
            # Leader
            readonly_fields = readonly_fields + ("leader",)
            if obj and obj.leader_id != request.user.id:
                # Participant on change
                readonly_fields = readonly_fields + ("name",)
        return readonly_fields

    def get_queryset(self, request: HttpRequest):
        projects_qs = super().get_queryset(request)
        if is_lab_admin(request.user):
            return projects_qs
        return projects_qs.filter(
            Q(leader=request.user)
            | Q(
                participation__user_id=request.user.id,
            )
        ).distinct()

    def get_inlines(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> List[Type[InlineModelAdmin]]:
        inlines = super().get_inlines(request, obj=obj)
        if obj and (is_lab_admin(request.user) or obj.leader_id == request.user.id):
            return inlines + [ParticipationInline]
        return inlines

    def get_form(
        self,
        request: Any,
        obj: Optional[Project] = ...,
        change: bool = ...,
        **kwargs: Any
    ):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        if "leader" in form.base_fields:
            form.base_fields["leader"].widget = UserWidgetWrapper(
                Select(),
                Project.leader.field.remote_field,
                self.admin_site,
            )
        return form

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
