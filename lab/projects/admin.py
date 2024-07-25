from typing import Any, Dict, Mapping, Optional, Type

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.db.models import Count, DateTimeField, Value
from django.forms.models import BaseInlineFormSet, ModelForm, inlineformset_factory
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from euphro_tools.hooks import initialize_project_directory, rename_project_directory
from lab.admin.mixins import LabPermission, LabPermissionMixin, LabRole
from lab.models import Participation
from lab.permissions import is_lab_admin, is_project_leader

from . import admin_filters
from .forms import (
    BaseParticipationForm,
    BaseProjectForm,
    BeamTimeRequestForm,
    LeaderParticipationForm,
    MemberProjectForm,
)
from .models import BeamTimeRequest, Project


class ProjectChangeList(ChangeList):
    def get_queryset(self, request: HttpRequest, exclude_parameters=None):
        qs = super().get_queryset(request, exclude_parameters)
        if request.method == "POST" and request.POST.get("action") == "delete_selected":
            return qs  # use more general queryset for delete action
        return (
            # qs with projects having at least one scheduled runs
            qs.filter(runs__start_date__isnull=False)  # type: ignore[attr-defined]
            .distinct()
            .annotate_first_run_date()
            .annotate(number_of_runs=Count("runs"))
            .order_by("-first_run_date")
        )


class ParticipationFormSet(BaseInlineFormSet):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        instance: Optional[Any] = None,
        save_as_new: bool = False,
        prefix: Optional[Any] = None,
        queryset: Optional[Any] = None,
        **kwargs: Any,
    ):
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
        return super().get_queryset().order_by("-is_leader", "created")

    def full_clean(self):
        for form in self:
            form.try_populate_institution()
        return super().full_clean()

    def save(self, commit: bool = True):
        # Set first participation as leader
        if len(self) > 0:
            self[0].instance.is_leader = True
        return super().save(commit)


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

    def get_related_project(  # type: ignore[override]
        self, obj: Project | None = None
    ) -> Project | None:
        return obj

    def get_formset(
        self,
        request: HttpRequest,
        obj: Optional[Project] = None,
        **kwargs: Mapping[str, Any],
    ):
        form = BaseParticipationForm if obj else LeaderParticipationForm

        formset: Type[BaseInlineFormSet] = inlineformset_factory(
            Project,
            Participation,
            form=form,  # type: ignore[arg-type]
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
    form = BeamTimeRequestForm
    fields = ("request_type", "request_id", "form_type", "problem_statement")

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(  # type: ignore[override]
        self,
        obj: Project | None = None,
    ) -> Project | None:
        return obj

    def has_delete_permission(
        self, request: HttpRequest, obj: Project | None = None  # type: ignore[override]
    ) -> bool:
        # should only add or edit
        return False


class ProjectDisplayMixin:
    @staticmethod
    @admin.display(description=_("Leader"))
    def leader_user(obj: Optional[Project]) -> Optional[User]:
        if obj and obj.leader:
            return obj.leader.user
        return None

    @staticmethod
    @admin.display(description=_("First run"))
    def first_run_date(obj: Optional[Project]):
        if obj:
            if hasattr(obj, "first_run_date"):  # from annotated queryset
                return obj.first_run_date
            run_dates = (
                obj.runs.filter(start_date__isnull=False)
                .order_by("start_date")
                .values_list("start_date", flat=True)
            )
            if run_dates:
                return run_dates[0]
        return ""

    @staticmethod
    @admin.display(description=_("First run date"))
    def first_run_date_with_link(obj: Project | None) -> str:
        date = ProjectDisplayMixin.first_run_date(obj)
        if not date:
            changelist_url = reverse("admin:lab_run_changelist")
            if obj:
                changelist_url += f"?project={obj.id}"
            return format_html(
                '{} <a href="{}" class="{}">{}</a>',
                _("No scheduled run."),
                changelist_url,
                "fr-link fr-link--sm",
                _("See runs"),
            )
        return date_format(date, format="SHORT_DATE_FORMAT", use_l10n=True)

    @staticmethod
    @admin.display(description=_("Runs"))
    def number_of_runs(obj: Optional[Project]) -> Optional[int]:
        if obj:
            if hasattr(obj, "number_of_runs"):
                return obj.number_of_runs  # from annotated queryset
            return obj.runs.count()
        return None


@admin.register(Project)
class ProjectAdmin(LabPermissionMixin, ProjectDisplayMixin, ModelAdmin):
    list_display = (
        "name",
        "admin",
        "leader_user",
        "first_run_date",
        "number_of_runs",
        "status",
    )
    readonly_fields = ("first_run_date_with_link",)

    lab_permissions = LabPermission(
        add_permission=LabRole.ANY_STAFF_USER,
        change_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    search_fields = ("name",)

    list_filter = [
        admin_filters.ProjectStatusListFilter,
        admin_filters.ProjectRunActiveEmbargoFilter,
    ]
    list_per_page = 20

    class Media:
        js = ("pages/project.js",)
        css = {"all": ("css/admin/project-admin.css",)}

    def get_related_project(  # type: ignore[override]
        self,
        obj: Project | None = None,
    ) -> Project | None:
        return obj

    def has_delete_permission(  # type: ignore[override]
        self, request: HttpRequest, obj: Project | None = None
    ) -> bool:
        return is_lab_admin(request.user)

    def get_fieldsets(self, request: HttpRequest, obj: Optional[Project] = None):
        basic_fields = (
            ["name", "admin", "comments", "first_run_date_with_link"]
            if obj
            else ["name"]
        )
        if is_lab_admin(request.user):
            basic_fields += ["confidential"]

        basic_fields_label = str(
            _("Basic information") if obj else _("Create new project")
        )
        fieldsets = [
            (
                basic_fields_label,
                {"fields": basic_fields},
            ),
        ]
        if not obj and not is_lab_admin(request.user):
            fieldsets += [
                (  # type: ignore[list-item]
                    None,
                    {
                        "fields": ["has_accepted_cgu"],
                        "description": "<p><strong>%s</strong></p>"  # type: ignore
                        % str(
                            _(
                                # pylint: disable=line-too-long
                                "To create a project on Euphrosyne, you are required to acknowledge and agree to the platform's general terms of use."
                            )
                        ),
                    },
                )
            ]

        return fieldsets

    def get_form(
        self,
        request: HttpRequest,
        obj: Optional[Project] = None,
        change: bool = False,
        **kwargs: dict[str, Any],
    ):
        if not obj:
            if is_lab_admin(request.user):
                return BaseProjectForm
            return MemberProjectForm
        return super().get_form(request, obj, change, **kwargs)

    def get_exclude(self, request: HttpRequest, obj: Optional[Project] = None):
        excluded = super().get_exclude(request, obj)
        if not is_lab_admin(request.user):
            return excluded + ("project",) if excluded else ("project",)  # type: ignore
        return excluded

    def get_readonly_fields(self, request: HttpRequest, obj: Optional[Project] = None):
        """Set edit permission based on user role."""
        readonly_fields = super().get_readonly_fields(request, obj)
        if not is_lab_admin(request.user):
            # Leader
            readonly_fields = (*readonly_fields, "name", "admin", "run_date")
        return readonly_fields

    def get_queryset(self, request: HttpRequest):
        projects_qs = super().get_queryset(request)
        if is_lab_admin(request.user):
            return projects_qs
        return projects_qs.filter(participation__user_id=request.user.id).distinct()

    def get_changelist(self, request, **kwargs):
        return ProjectChangeList

    def get_inlines(self, request: HttpRequest, obj: Project | None = None):
        inlines = []
        if obj:
            if is_lab_admin(request.user) or is_project_leader(
                request.user, obj  # type: ignore[arg-type]
            ):
                inlines += [ParticipationInline]  # type: ignore[list-item]
            inlines += [BeamTimeRequestInline]  # type: ignore[list-item]
        return inlines

    def save_model(
        self,
        request: HttpRequest,
        obj: Project,
        form: ModelForm,
        change: bool,
    ):
        if not change and is_lab_admin(request.user):
            obj.admin_id = request.user.id  # type: ignore[assignment]
        obj.save()
        if not change:
            if not is_lab_admin(request.user):
                obj.participation_set.create(
                    user=request.user,  # type: ignore[misc]
                    is_leader=True,
                )
            initialize_project_directory(obj.name)
        if change and "name" in form.changed_data:
            rename_project_directory(form.initial["name"], obj.name)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        return super().changeform_view(
            request,
            object_id,
            form_url,
            {
                **(extra_context if extra_context else {}),
                "show_save": True,
                "show_save_as_new": False,
                "show_save_and_add_another": False,
            },
        )

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[Dict[str, str]] = None
    ):
        changelist_view = super().changelist_view(
            request,
            {
                **(extra_context if extra_context else {}),
                "title": _("Projects"),
                "has_delete_permission": self.has_delete_permission(request),
                "extra_qs": [],
            },
        )

        if not hasattr(
            changelist_view, "context_data"
        ) or not changelist_view.context_data.get("cl"):
            # when actions (i.e delete) request
            return changelist_view

        cl = changelist_view.context_data.get("cl")
        changelist_view.context_data["has_data"] = cl.full_result_count > 0
        if cl and not cl.has_active_filters and not cl.query and not cl.page_num > 1:
            # add scheduled projects on basic page (no search or pagination)
            to_schedule_projects = (
                self.get_queryset(request)
                .has_to_schedule_runs()
                .annotate(
                    first_run_date=Value(
                        None,
                        output_field=DateTimeField(),
                    )
                )  # db query optimization
                .annotate(number_of_runs=Count("runs"))
                .order_by("-created")
                .distinct()
            )
            changelist_view.context_data["extra_qs"].append(
                {"qs": to_schedule_projects, "title": _("To schedule")}
            )
        changelist_view.context_data["has_data"] = any(
            [
                changelist_view.context_data["has_data"],
                *[len(qs["qs"]) > 0 for qs in changelist_view.context_data["extra_qs"]],
            ]
        )
        return changelist_view

    def get_field_queryset(
        self, db: str | None, db_field, request: HttpRequest
    ) -> Optional[Any]:
        qs = super().get_field_queryset(db, db_field, request)
        if qs and db_field == Project.admin.field:
            return qs.filter(is_lab_admin=True)
        return qs
