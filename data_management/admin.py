from datetime import datetime
from uuid import UUID

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import (
    CharField,
    DateTimeField,
    F,
    OuterRef,
    QuerySet,
    Subquery,
    UUIDField,
)
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabAdminAllowedMixin

from .models import (
    LifecycleOperation,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)

BADGE_CLASS_BY_STATE: dict[str, str] = {
    LifecycleState.HOT: "fr-badge fr-badge--success fr-badge--no-icon fr-badge--sm",
    LifecycleState.COOLING: "fr-badge fr-badge--info fr-badge--no-icon fr-badge--sm",
    LifecycleState.COOL: "fr-badge fr-badge--no-icon fr-badge--sm",
    LifecycleState.RESTORING: "fr-badge fr-badge--info fr-badge--no-icon fr-badge--sm",
    LifecycleState.ERROR: "fr-badge fr-badge--error fr-badge--no-icon fr-badge--sm",
}

LIFECYCLE_STATE_LABEL_BY_STATE: dict[str, str] = {
    LifecycleState.HOT: gettext("available"),
    LifecycleState.COOL: gettext("archived"),
    LifecycleState.COOLING: gettext("archiving"),
    LifecycleState.RESTORING: gettext("restoring"),
    LifecycleState.ERROR: gettext("error"),
}


def _workplace_url(project_id: int) -> str:
    return reverse("admin:lab_project_workplace", args=[project_id])


def _lifecycle_operation_change_url(operation_id: str) -> str:
    return reverse(
        "admin:data_management_lifecycleoperation_change", args=[operation_id]
    )


class ProjectDataCoolingEligibilityListFilter(admin.SimpleListFilter):
    class FilterValues:
        ELIGIBLE = "eligible"
        NOT_ELIGIBLE = "not_eligible"

    title = _("eligible for cooling")
    parameter_name = "cooling_eligibility"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return [
            (self.FilterValues.ELIGIBLE, _("Yes")),
            (self.FilterValues.NOT_ELIGIBLE, _("No")),
        ]

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[ProjectData],
    ) -> QuerySet[ProjectData]:
        value = self.value()
        if not value:
            return queryset

        if value == self.FilterValues.ELIGIBLE:
            return queryset.filter(cooling_eligible_at__lte=timezone.now())
        return queryset.exclude(cooling_eligible_at__lte=timezone.now())


class ProjectDataLifecycleStateListFilter(admin.SimpleListFilter):
    title = _("lifecycle state")
    parameter_name = "lifecycle_state"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return [
            (
                enum_member.value,
                capfirst(LIFECYCLE_STATE_LABEL_BY_STATE[enum_member.value]),
            )
            for enum_member in LifecycleState
        ]

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[ProjectData],
    ) -> QuerySet[ProjectData]:
        if not self.value():
            return queryset
        return queryset.filter(lifecycle_state=self.value())


class LifecycleOperationProjectDataListFilter(admin.SimpleListFilter):
    title = _("project")
    parameter_name = "project_data"

    def lookups(self, request, model_admin):
        return ()

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[LifecycleOperation],
    ) -> QuerySet[LifecycleOperation]:
        value = self.value()
        if not value:
            return queryset
        return queryset.filter(project_data_id=value)  # type: ignore


@admin.register(ProjectData)
class ProjectDataAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    change_list_template = "admin/data_management/projectdata/change_list.html"
    list_display = (
        "project_link",
        "lifecycle_state_badge",
        "cooling_eligible_at",
        "last_operation_lifecycle",
        "last_operation",
    )
    list_display_links = None
    list_filter = (
        ProjectDataLifecycleStateListFilter,
        ProjectDataCoolingEligibilityListFilter,
    )
    search_fields = ("project__name", "project__slug")
    ordering = ("cooling_eligible_at", "project__name")

    def get_queryset(self, request: HttpRequest):
        last_operation_queryset = (
            LifecycleOperation.objects.filter(project_data_id=OuterRef("pk"))
            .annotate(operation_sort_ts=Coalesce("started_at", "finished_at"))
            .order_by(
                F("operation_sort_ts").desc(nulls_last=True),
                F("finished_at").desc(nulls_last=True),
            )
        )
        return (
            super()
            .get_queryset(request)
            .select_related("project")
            .annotate(
                last_operation_id=Subquery(
                    last_operation_queryset.values("operation_id")[:1],
                    output_field=UUIDField(),
                ),
                last_operation_type=Subquery(
                    last_operation_queryset.values("type")[:1],
                    output_field=CharField(),
                ),
                last_operation_datetime=Subquery(
                    last_operation_queryset.values("operation_sort_ts")[:1],
                    output_field=DateTimeField(),
                ),
            )
        )

    def changelist_view(self, request: HttpRequest, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = gettext("Project data lifecycle")
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context=None,
    ) -> HttpResponseRedirect:
        project_data = self.get_object(request, object_id)
        if project_data is None:
            raise Http404
        if not self.has_view_permission(request, obj=project_data):
            raise PermissionDenied
        return HttpResponseRedirect(_workplace_url(project_data.project_id))

    @admin.display(description=_("Project"))
    def project_link(self, obj: ProjectData) -> str:
        return format_html(
            '<a href="{}">{}</a>',
            _workplace_url(obj.project_id),
            obj.project,
        )

    @admin.display(description=_("lifecycle state"), ordering="lifecycle_state")
    def lifecycle_state_badge(self, obj: ProjectData) -> str:
        return self._render_lifecycle_state_badge(obj.lifecycle_state)

    @staticmethod
    def _render_lifecycle_state_badge(lifecycle_state: str) -> str:
        return format_html(
            '<span class="{}">{}</span>',
            BADGE_CLASS_BY_STATE[lifecycle_state],
            LIFECYCLE_STATE_LABEL_BY_STATE[lifecycle_state],
        )

    @staticmethod
    def _get_last_operation_type(
        obj: ProjectData,
    ) -> str | None:
        return obj.last_operation_type  # type: ignore[attr-defined]

    @staticmethod
    def _get_last_operation_datetime(
        obj: ProjectData,
    ) -> datetime | None:
        return obj.last_operation_datetime  # type: ignore[attr-defined]

    @staticmethod
    def _get_last_operation_id(obj: ProjectData) -> UUID | None:
        return obj.last_operation_id  # type: ignore[attr-defined]

    @admin.display(description=_("Last operation lifecycle"))
    def last_operation_lifecycle(self, obj: ProjectData) -> str | None:
        operation_type = self._get_last_operation_type(obj)
        if operation_type is None:
            return None
        old_state, new_state = self._operation_lifecycle_states(operation_type)
        accessible_transition_label = _("%(old_state)s to %(new_state)s") % {
            "old_state": LIFECYCLE_STATE_LABEL_BY_STATE[old_state],
            "new_state": LIFECYCLE_STATE_LABEL_BY_STATE[new_state],
        }
        return format_html(
            '<span class="fr-sr-only">{}</span>'
            '<span aria-hidden="true">{} <span>&rarr;</span> {}</span>',
            accessible_transition_label,
            self._render_lifecycle_state_badge(old_state),
            self._render_lifecycle_state_badge(new_state),
        )

    @admin.display(description=_("Last operation"), ordering="last_operation_datetime")
    def last_operation(self, obj: ProjectData) -> str | None:
        operation_id = self._get_last_operation_id(obj)
        operation_datetime = self._get_last_operation_datetime(obj)
        if operation_id is None or operation_datetime is None:
            return None
        return format_html(
            '<a href="{}">{}</a>',
            _lifecycle_operation_change_url(str(operation_id)),
            date_format(
                operation_datetime,
                format="SHORT_DATETIME_FORMAT",
                use_l10n=True,
            ),
        )

    @staticmethod
    def _operation_lifecycle_states(operation_type: str) -> tuple[str, str]:
        if operation_type == LifecycleOperationType.COOL:
            return (LifecycleState.HOT, LifecycleState.COOL)
        return (LifecycleState.COOL, LifecycleState.HOT)


@admin.register(LifecycleOperation)
class LifecycleOperationAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = (
        "operation_id",
        "project_link",
        "type",
        "status",
        "started_at",
        "finished_at",
        "bytes_progress",
        "files_progress",
    )
    list_filter = (
        LifecycleOperationProjectDataListFilter,
        "type",
        "status",
    )
    search_fields = (
        "operation_id",
        "project_data__project__name",
        "project_data__project__slug",
    )
    ordering = ("-started_at", "-finished_at")
    fields = (
        "operation_id",
        "project_link",
        "type",
        "status",
        "started_at",
        "finished_at",
        "bytes_total",
        "files_total",
        "bytes_copied",
        "files_copied",
        "error_message",
        "formatted_error_details",
    )
    readonly_fields = fields

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        return {}

    def get_queryset(self, request: HttpRequest):
        queryset = super().get_queryset(request).select_related("project_data__project")
        project_data_id = request.GET.get("project_data")
        if project_data_id:
            return queryset.filter(project_data_id=project_data_id)
        return queryset

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    @admin.display(description=_("Project"))
    def project_link(self, obj: LifecycleOperation) -> str:
        return format_html(
            '<a href="{}" class="fr-link">{}</a>',
            _workplace_url(obj.project_data.project_id),
            obj.project_data.project.name,
        )

    @admin.display(description=_("Bytes moved"))
    def bytes_progress(self, obj: LifecycleOperation) -> str:
        copied_display = obj.bytes_copied if obj.bytes_copied is not None else "-"
        total_display = obj.bytes_total if obj.bytes_total is not None else "-"
        return f"{copied_display} / {total_display}"

    @admin.display(description=_("Files moved"))
    def files_progress(self, obj: LifecycleOperation) -> str:
        copied_display = obj.files_copied if obj.files_copied is not None else "-"
        total_display = obj.files_total if obj.files_total is not None else "-"
        return f"{copied_display} / {total_display}"

    @admin.display(description=_("Error details"))
    def formatted_error_details(self, obj: LifecycleOperation) -> str | None:
        if not obj.error_details:
            return None
        return format_html("<pre>{}</pre>", obj.error_details)
