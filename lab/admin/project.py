from typing import Any, Dict, List, Mapping, Optional, Tuple, Type

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
from django.forms.models import BaseInlineFormSet, ModelForm, inlineformset_factory
from django.http.request import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from lab.widgets import LeaderReadonlyWidget

from ..forms import (
    BaseParticipationForm,
    LeaderParticipationForm,
    RunDetailsForm,
    RunStatusAdminForm,
    RunStatusMemberForm,
)
from ..models import BeamTimeRequest, Participation, Project, Run
from ..permissions import is_lab_admin, is_project_leader
from .mixins import LabPermission, LabPermissionMixin, LabRole
from .run import BASE_RUN_FIELDSETS


class ParticipationFormSet(BaseInlineFormSet):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        instance: Optional[Any] = None,
        save_as_new: bool = None,
        prefix: Optional[Any] = None,
        queryset: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(
            data=data,
            files=files,
            instance=instance,
            save_as_new=save_as_new,
            prefix=prefix,
            queryset=queryset,
            **kwargs
        )
        for form in self:
            if form.instance.is_leader and "DELETE" in form.fields:
                form.fields["DELETE"].disabled = True

    def get_queryset(self):
        return super().get_queryset().order_by("-is_leader")


class ParticipationInline(LabPermissionMixin, admin.TabularInline):
    model = Participation
    verbose_name = _("Project member")

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_LEADER,
        change_permission=LabRole.PROJECT_LEADER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj

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
            formset=ParticipationFormSet,
        )
        return formset


class BeamTimeRequestInline(LabPermissionMixin, admin.StackedInline):
    model = BeamTimeRequest
    fields = ("request_type", "request_id", "form_type", "problem_statement")

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj


class RunInline(LabPermissionMixin, admin.StackedInline):
    model = Run
    extra = 0
    show_change_link = True
    readonly_fields = RunDetailsForm.Meta.fields
    fieldsets = BASE_RUN_FIELDSETS
    template = "admin/edit_inline/stacked_run_in_project.html"

    lab_permissions = LabPermission(
        change_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> bool:
        """Disable adding a new run through the inline, force the user to go
        through the Run admin page
        """
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> bool:
        return False

    def get_formset(
        self,
        request: HttpRequest,
        obj: Optional[Project] = ...,
        **kwargs: Mapping[str, Any]
    ):
        self.form = (
            RunStatusAdminForm if is_lab_admin(request.user) else RunStatusMemberForm
        )
        return super().get_formset(request, obj, **kwargs)


# Allowance: ADMIN:lab admin, EDITOR:project leader, VIEWER:project member
@admin.register(Project)
class ProjectAdmin(LabPermissionMixin, ModelAdmin):
    list_display = ("name", "leader_user", "status")
    readonly_fields = ("members", "status", "editable_leader_user", "leader_user")

    lab_permissions = LabPermission(
        add_permission=LabRole.ANY_STAFF_USER,
        change_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    @staticmethod
    @admin.display(description=_("Leader"))
    def leader_user(obj: Optional[Project]) -> Optional[User]:
        if obj and obj.leader:
            return obj.leader.user
        return None

    @staticmethod
    @admin.display(description=_("Leader"))
    def editable_leader_user(obj: Optional[Project]) -> str:
        return format_html(
            LeaderReadonlyWidget().render(
                context={
                    "user": obj.leader.user if obj.leader else None,
                    "project_id": obj.id,
                }
            )
        )

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj

    def get_fieldsets(
        self, request: HttpRequest, obj: Optional[Project] = ...
    ) -> List[Tuple[Optional[str], Dict[str, Any]]]:
        return [
            (
                _("Basic information"),
                {
                    "fields": (
                        "name",
                        "status",
                        "admin",
                        "comments",
                        "editable_leader_user"
                        if is_lab_admin(request.user)
                        else "leader_user",
                        "members",
                    )
                },
            ),
        ]

    def get_exclude(self, request: HttpRequest, obj: Optional[Project] = None):
        excluded = super().get_exclude(request, obj)
        if not is_lab_admin(request.user):
            return excluded + ("project",) if excluded else ("project",)
        return excluded

    def get_readonly_fields(self, request: HttpRequest, obj: Optional[Project] = None):
        """Set edit permission based on user role."""
        readonly_fields = super().get_readonly_fields(request, obj)
        if not is_lab_admin(request.user):
            # Leader
            readonly_fields = readonly_fields + ("admin", "run_date")
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
        if is_lab_admin(request.user) or (obj and is_project_leader(request.user, obj)):
            inlines += [ParticipationInline]
        if obj:
            inlines += [BeamTimeRequestInline, RunInline]
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
