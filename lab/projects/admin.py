import json
from typing import Any, Optional

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.db.models import Count, DateTimeField, Value
from django.forms.models import ModelForm
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from euphro_tools.hooks import (
    RenameFailedError,
    initialize_project_directory,
    rename_project_directory,
)
from lab.admin.mixins import LabPermission, LabPermissionMixin, LabRole
from lab.participations.models import Employer
from lab.permissions import is_lab_admin

from . import admin_filters, inlines
from .forms import (
    BaseProjectForm,
    MemberProjectForm,
)
from .models import Project


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
            .select_related("admin")  # Add select_related for admin user
            .with_prefetched_leaders()  # Use optimized prefetch for leaders
            .prefetch_related("runs")
            .order_by("-first_run_date")
        )


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
            # Use annotated value if available (most efficient)
            if hasattr(obj, "first_run_date"):
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
                return obj.number_of_runs
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
            else ["name", "comments"]
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
                (
                    "",
                    {
                        "fields": ["institution"],
                        # pylint: disable=line-too-long
                        "description": str(_("Project leader institution")),  # type: ignore
                    },
                ),
                (
                    "",
                    {
                        "fields": [
                            (  # type: ignore
                                "employer_first_name",
                                "employer_last_name",
                            ),
                            "employer_email",
                            "employer_function",
                        ],
                        # pylint: disable=line-too-long
                        "description": str(_("Employer information")),  # type: ignore
                    },
                ),
                (
                    "",
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
                ),
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
            readonly_fields = (*readonly_fields, "admin", "run_date")
            if obj:
                readonly_fields = (*readonly_fields, "name")
        return readonly_fields

    def get_queryset(self, request: HttpRequest):
        projects_qs = super().get_queryset(request)
        if is_lab_admin(request.user):
            return projects_qs
        return projects_qs.filter(participation__user_id=request.user.id).distinct()

    def get_changelist(self, request, **kwargs):
        return ProjectChangeList

    def get_inlines(self, request: HttpRequest, obj: Optional[Project] = None):
        if obj:
            return [inlines.BeamTimeRequestInline]  # type: ignore[list-item]
        return []

    def save_model(
        self,
        request: HttpRequest,
        obj: Project,
        form: ModelForm,
        change: bool,
    ):
        if not change and is_lab_admin(request.user):
            obj.admin_id = request.user.id  # type: ignore[assignment]

        if change and "name" in form.changed_data:
            try:
                rename_project_directory(form.initial["name"], obj.name)
            except RenameFailedError as error:
                # Prevent changing name
                obj.name = form.initial["name"]
                self.message_user(
                    request,
                    message=_("Renaming this project is not posible for now : %s")
                    % str(error),
                    level=messages.ERROR,
                )

        obj.save()
        if not change:
            if not is_lab_admin(request.user):
                employer = Employer.objects.create(
                    first_name=form.cleaned_data["employer_first_name"],
                    last_name=form.cleaned_data["employer_last_name"],
                    email=form.cleaned_data["employer_email"],
                    function=form.cleaned_data["employer_function"],
                )
                obj.participation_set.create(
                    user=request.user,  # type: ignore[misc]
                    institution=form.cleaned_data[
                        "institution"
                    ],  # institution is set in form, throw error otherwise
                    is_leader=True,
                    on_premises=True,
                    employer=employer,
                )
            initialize_project_directory(obj.name)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        view = super().changeform_view(
            request,
            object_id,
            form_url,
            {
                **(extra_context if extra_context else {}),
                "show_save": True,
                "show_save_as_new": False,
                "show_save_and_add_another": False,
                "json_data": json.dumps(
                    {"projectId": object_id} if object_id else None
                ),
            },
        )
        if (
            not object_id
            and hasattr(view, "context_data")
            and not is_lab_admin(request.user)
        ):
            last_participation = request.user.participation_set.order_by(
                "-created"
            ).first()
            if last_participation and last_participation.institution:
                view.context_data["adminform"].fields[
                    "institution"
                ].widget.instance = last_participation.institution
                if last_participation.employer:
                    for field in [
                        "first_name",
                        "last_name",
                        "email",
                        "function",
                    ]:
                        view.context_data["adminform"].fields[
                            f"employer_{field}"
                        ].initial = getattr(last_participation.employer, field)

        return view

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, str] | None = None
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
                .select_related("admin")  # Add select_related for admin user
                .with_prefetched_leaders()  # Use optimized prefetch for leaders
                .prefetch_related("runs")
                .order_by("-created")
                .distinct()
            )
            # Use select_related and prefetch_related to reduce database queries
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
