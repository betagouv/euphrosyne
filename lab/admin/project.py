from typing import Any, List, Mapping, Optional, Type

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
from django.forms.models import ModelForm, inlineformset_factory
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User

from ..forms import BaseParticipationForm, LeaderParticipationForm
from ..lib import is_lab_admin
from ..models import BeamTimeRequest, Participation, Project


class ParticipationInline(admin.TabularInline):
    model = Participation
    verbose_name = _("Project member")

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


class BeamTimeRequestInline(admin.StackedInline):
    model = BeamTimeRequest
    fields = ("request_type", "request_id", "form_type", "problem_statement")

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> bool:
        return obj and (
            is_lab_admin(request.user) or obj.leader.user_id == request.user.id
        )

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> bool:
        return obj and (
            is_lab_admin(request.user) or obj.leader.user_id == request.user.id
        )


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:project member
@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ("name", "leader_user", "status")
    readonly_fields = ("members", "status", "leader_user")
    fieldsets = (
        (
            _("Basic information"),
            {
                "fields": (
                    "name",
                    "status",
                    "admin",
                    "comments",
                    "leader_user",
                    "members",
                )
            },
        ),
    )

    @staticmethod
    @admin.display(description=_("Leader"))
    def leader_user(obj: Optional[Project]) -> Optional[User]:
        if obj and obj.leader:
            return obj.leader.user
        return None

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
            # Leader
            readonly_fields = readonly_fields + ("admin", "run_date")
            if obj and obj.leader.user_id != request.user.id:
                # Participant on change
                readonly_fields = readonly_fields + ("name", "comments")
        return readonly_fields

    def get_queryset(self, request: HttpRequest):
        projects_qs = super().get_queryset(request)
        if is_lab_admin(request.user):
            return projects_qs
        return projects_qs.filter(participation__user_id=request.user.id).distinct()

    def get_inlines(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> List[Type[InlineModelAdmin]]:
        inlines = []
        if is_lab_admin(request.user) or (
            obj and obj.leader.user_id == request.user.id
        ):
            inlines += [ParticipationInline]
        if obj:
            inlines += [BeamTimeRequestInline]
        return inlines

    def save_model(
        self,
        request: HttpRequest,
        obj: Project,
        form: ModelForm,
        change: bool,
    ) -> None:
        if not change and is_lab_admin(request.user):
            obj.admin_id = request.user.id
        obj.save()
        if not change and not is_lab_admin(request.user):
            obj.participation_set.create(user_id=request.user.id, is_leader=True)
