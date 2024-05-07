from typing import Any, Mapping, Optional

from django.contrib import admin
from django.db.models.query import QuerySet
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabPermission, LabPermissionMixin, LabRole
from lab.models import Participation

from .forms import BaseParticipationForm, BeamTimeRequestForm, LeaderParticipationForm
from .models import BeamTimeRequest, Project


class ParticipationFormSet(BaseInlineFormSet):
    model = Participation

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        instance: Optional[Any] = None,
        save_as_new: bool = None,
        prefix: Optional[Any] = None,
        queryset: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            files=files,
            instance=instance,
            save_as_new=save_as_new,
            prefix=prefix,
            queryset=queryset,
            **kwargs,
        )
        for form in self:
            if form.instance.is_leader and "DELETE" in form.fields:
                form.fields["DELETE"].disabled = True

    def get_queryset(self):
        return super().get_queryset().order_by("created")

    def full_clean(self):
        for form in self:
            form.try_populate_institution()
        return super().full_clean()


class LeaderParticipationFormSet(ParticipationFormSet):
    def save(self, commit: bool = True):
        # Set first participation as leader
        if len(self) > 0:
            self[0].instance.is_leader = True
            self[0].instance.on_premises = True
        return super().save(commit)


class OnPremisesParticipationFormSet(ParticipationFormSet):
    def save(self, commit: bool = True):
        # Set first participation as leader
        for form in self:
            form.instance.on_premises = True
        return super().save(commit)


class MemberParticipationInline(LabPermissionMixin, admin.TabularInline):
    model = Participation
    verbose_name = _("project member")
    verbose_name_plural = _("project members")

    template = "admin/edit_inline/tabular_participation_in_project.html"

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_LEADER,
        change_permission=LabRole.PROJECT_LEADER,
        view_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_LEADER,
    )

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj

    def get_formset(
        self,
        request: HttpRequest,
        obj: Optional[Project] = None,
        **kwargs: Mapping[str, Any],
    ):
        form = BaseParticipationForm

        formset_class = (
            self.formset
            if self.formset and self.formset != BaseInlineFormSet
            else ParticipationFormSet
        )
        formset = inlineformset_factory(
            Project,
            Participation,
            form=form,
            extra=0,
            min_num=0,
            max_num=1000,
            can_delete=bool(obj),
            formset=formset_class,
        )
        return formset


class OnPremisesParticipationInline(MemberParticipationInline):
    verbose_name = _("on premises member")
    verbose_name_plural = _("on premises members")

    formset = OnPremisesParticipationFormSet

    def get_queryset(self, request: HttpRequest) -> QuerySet[Participation]:
        return super().get_queryset(request).filter(is_leader=False, on_premises=True)


class RemoteParticipationInline(MemberParticipationInline):
    verbose_name = _("remote member")
    verbose_name_plural = _("remote members")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Participation]:
        return super().get_queryset(request).filter(is_leader=False, on_premises=False)


class LeaderParticipationInline(LabPermissionMixin, admin.TabularInline):
    model = Participation
    verbose_name = _("project leader")

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_LEADER,
        change_permission=LabRole.LAB_ADMIN,
        view_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_LEADER,
    )

    template = "admin/edit_inline/tabular_participation_in_project.html"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Participation]:
        return super().get_queryset(request).filter(is_leader=True)

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj

    def get_formset(
        self,
        request: HttpRequest,
        obj: Optional[Project] = None,
        **kwargs: Mapping[str, Any],
    ):
        form = LeaderParticipationForm

        formset = inlineformset_factory(
            Project,
            Participation,
            form=form,
            extra=0,
            min_num=1,
            # On creation, only leader participation can be added
            max_num=1,
            can_delete=False,
            formset=LeaderParticipationFormSet,
        )
        return formset


class ParticipationInline(LabPermissionMixin, admin.TabularInline):
    model = Participation
    verbose_name = _("Project member")
    verbose_name_plural = _("Project members")
    template = "admin/edit_inline/tabular_participation_in_project.html"

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_LEADER,
        change_permission=LabRole.LAB_ADMIN,
        view_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_LEADER,
    )

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).filter(is_leader=False)

    def get_formset(
        self,
        request: HttpRequest,
        obj: Optional[Project] = None,
        **kwargs: Mapping[str, Any],
    ):
        form = BaseParticipationForm

        formset = inlineformset_factory(
            Project,
            Participation,
            form=form,
            extra=0,
            min_num=1,
            # On creation, only leader participation can be added
            max_num=1000,
            can_delete=bool(obj),
            formset=ParticipationFormSet,
        )
        return formset


class BeamTimeRequestInline(LabPermissionMixin, admin.StackedInline):
    model = BeamTimeRequest
    form = BeamTimeRequestForm
    fields = ("request_type", "request_id", "form_type", "problem_statement")

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(self, obj: Optional[Project] = None) -> Optional[Project]:
        return obj

    def has_delete_permission(
        self, request: HttpRequest, obj: Project | None = None
    ) -> bool:
        # should only add or edit
        return False
