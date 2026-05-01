from datetime import datetime
from uuid import UUID

from django.contrib import admin, messages
from django.contrib.admin import helpers
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
from django.template.defaultfilters import filesizeformat
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabAdminAllowedMixin

from .models import (
    FromDataDeletionStatus,
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)
from .operations import (
    FromDataDeletionNotAllowedError,
    FromDataDeletionStartError,
    trigger_from_data_deletion,
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

OPERATION_STATUS_BADGE_CLASS_BY_STATUS: dict[str, str] = {
    LifecycleOperationStatus.PENDING: (
        "fr-badge fr-badge--info fr-badge--no-icon fr-badge--sm"
    ),
    LifecycleOperationStatus.RUNNING: (
        "fr-badge fr-badge--info fr-badge--no-icon fr-badge--sm"
    ),
    LifecycleOperationStatus.SUCCEEDED: (
        "fr-badge fr-badge--success fr-badge--no-icon fr-badge--sm"
    ),
    LifecycleOperationStatus.FAILED: (
        "fr-badge fr-badge--error fr-badge--no-icon fr-badge--sm"
    ),
}

FROM_DATA_DELETION_STATUS_BADGE_CLASS_BY_STATUS: dict[str, str] = {
    FromDataDeletionStatus.NOT_REQUESTED: ("fr-badge fr-badge--no-icon fr-badge--sm"),
    FromDataDeletionStatus.RUNNING: (
        "fr-badge fr-badge--info fr-badge--no-icon fr-badge--sm"
    ),
    FromDataDeletionStatus.SUCCEEDED: (
        "fr-badge fr-badge--success fr-badge--no-icon fr-badge--sm"
    ),
    FromDataDeletionStatus.FAILED: (
        "fr-badge fr-badge--error fr-badge--no-icon fr-badge--sm"
    ),
}

OPERATION_TYPE_BADGE_CLASS_BY_TYPE: dict[str, str] = {
    LifecycleOperationType.COOL: "fr-badge fr-badge--no-icon fr-badge--sm",
    LifecycleOperationType.RESTORE: (
        "fr-badge fr-badge--info fr-badge--no-icon fr-badge--sm"
    ),
}


def _workplace_url(project_id: int) -> str:
    return reverse("admin:lab_project_workplace", args=[project_id])


def _lifecycle_operation_change_url(operation_id: str) -> str:
    return reverse(
        "admin:data_management_lifecycleoperation_change", args=[operation_id]
    )


@admin.action(permissions=["view"], description=_("Delete source data"))
def delete_source_data(
    modeladmin: "LifecycleOperationAdmin",
    request: HttpRequest,
    queryset: QuerySet[LifecycleOperation],
):
    if request.POST.get("post"):
        started_count = 0
        for operation in queryset:
            try:
                trigger_from_data_deletion(operation.operation_id)
            except FromDataDeletionNotAllowedError as error:
                modeladmin.message_user(
                    request,
                    _(
                        "Could not delete source data for operation "
                        "%(operation_id)s: %(detail)s"
                    )
                    % {
                        "operation_id": error.operation.operation_id,
                        "detail": error.detail,
                    },
                    level=messages.ERROR,
                )
                continue
            except FromDataDeletionStartError as error:
                modeladmin.message_user(
                    request,
                    _(
                        "Could not start source data deletion for operation "
                        "%(operation_id)s: %(detail)s"
                    )
                    % {
                        "operation_id": error.operation.operation_id,
                        "detail": error.detail,
                    },
                    level=messages.ERROR,
                )
                continue

            started_count += 1

        if started_count:
            modeladmin.message_user(
                request,
                _("Started source data deletion for %(count)d operation(s).")
                % {"count": started_count},
                level=messages.SUCCESS,
            )
        return None

    context = {
        **modeladmin.admin_site.each_context(request),
        "title": _("Delete source data"),
        "subtitle": None,
        "opts": modeladmin.model._meta,
        "queryset": queryset,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "media": modeladmin.media,
    }
    request.current_app = modeladmin.admin_site.name
    return TemplateResponse(
        request,
        modeladmin.delete_source_data_confirmation_template,
        context,
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
    template = "admin/lab/project/filter.html"

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


class LifecycleOperationTypeListFilter(admin.SimpleListFilter):
    title = _("operation type")
    parameter_name = "type"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return LifecycleOperationType.choices

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[LifecycleOperation],
    ) -> QuerySet[LifecycleOperation]:
        if not self.value():
            return queryset
        return queryset.filter(type=self.value())


class LifecycleOperationStatusListFilter(admin.SimpleListFilter):
    title = _("operation status")
    parameter_name = "status"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return LifecycleOperationStatus.choices

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[LifecycleOperation],
    ) -> QuerySet[LifecycleOperation]:
        if not self.value():
            return queryset
        return queryset.filter(status=self.value())


class FromDataDeletionStatusListFilter(admin.SimpleListFilter):
    title = _("source data deletion")
    parameter_name = "from_data_deletion_status"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return FromDataDeletionStatus.choices

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[LifecycleOperation],
    ) -> QuerySet[LifecycleOperation]:
        if not self.value():
            return queryset
        return queryset.filter(from_data_deletion_status=self.value())


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
    actions = [delete_source_data]
    change_list_template = "admin/data_management/lifecycleoperation/change_list.html"
    delete_source_data_confirmation_template = (
        "admin/data_management/lifecycleoperation/delete_source_data_confirmation.html"
    )
    list_display = (
        "operation_id_display",
        "project_link",
        "operation_type_badge",
        "status_badge",
        "started_at_display",
        "finished_at_display",
        "from_data_deletion_status_badge",
        "from_data_deleted_at_display",
        "bytes_progress",
        "files_progress",
    )
    list_filter = (
        LifecycleOperationProjectDataListFilter,
        LifecycleOperationTypeListFilter,
        LifecycleOperationStatusListFilter,
        FromDataDeletionStatusListFilter,
    )
    search_fields = (
        "operation_id",
        "project_data__project__name",
        "project_data__project__slug",
    )
    ordering = ("-started_at", "-finished_at")
    fields = (
        "operation_id_display",
        "project_link",
        "operation_type_badge",
        "status_badge",
        "started_at_display",
        "finished_at_display",
        "bytes_total_display",
        "files_total_display",
        "bytes_copied_display",
        "files_copied_display",
        "from_data_deletion_status_badge",
        "from_data_deleted_at_display",
        "from_data_deletion_error_display",
        "error_message_display",
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

    @admin.display(description=_("Operation ID"), ordering="operation_id")
    def operation_id_display(self, obj: LifecycleOperation) -> UUID:
        return obj.operation_id

    @admin.display(description=_("Project"))
    def project_link(self, obj: LifecycleOperation) -> str:
        return format_html(
            '<a href="{}" class="fr-link">{}</a>',
            _workplace_url(obj.project_data.project_id),
            obj.project_data.project.name,
        )

    @admin.display(description=_("Type"), ordering="type")
    def operation_type_badge(self, obj: LifecycleOperation) -> str:
        return format_html(
            '<span class="{}">{}</span>',
            OPERATION_TYPE_BADGE_CLASS_BY_TYPE[obj.type],
            obj.get_type_display(),
        )

    @admin.display(description=_("Status"), ordering="status")
    def status_badge(self, obj: LifecycleOperation) -> str:
        return format_html(
            '<span class="{}">{}</span>',
            OPERATION_STATUS_BADGE_CLASS_BY_STATUS[obj.status],
            obj.get_status_display(),
        )

    @admin.display(
        description=_("Source deletion"),
        ordering="from_data_deletion_status",
    )
    def from_data_deletion_status_badge(self, obj: LifecycleOperation) -> str:
        return format_html(
            '<span class="{}">{}</span>',
            FROM_DATA_DELETION_STATUS_BADGE_CLASS_BY_STATUS[
                obj.from_data_deletion_status
            ],
            obj.get_from_data_deletion_status_display(),
        )

    @admin.display(description=_("Started at"), ordering="started_at")
    def started_at_display(self, obj: LifecycleOperation) -> datetime | None:
        return obj.started_at

    @admin.display(description=_("Finished at"), ordering="finished_at")
    def finished_at_display(self, obj: LifecycleOperation) -> datetime | None:
        return obj.finished_at

    @admin.display(description=_("Total bytes"), ordering="bytes_total")
    def bytes_total_display(self, obj: LifecycleOperation) -> str:
        return self._format_bytes(obj.bytes_total)

    @admin.display(description=_("Total files"), ordering="files_total")
    def files_total_display(self, obj: LifecycleOperation) -> int | None:
        return obj.files_total

    @admin.display(description=_("Copied bytes"), ordering="bytes_copied")
    def bytes_copied_display(self, obj: LifecycleOperation) -> str:
        return self._format_bytes(obj.bytes_copied)

    @admin.display(description=_("Copied files"), ordering="files_copied")
    def files_copied_display(self, obj: LifecycleOperation) -> int | None:
        return obj.files_copied

    @admin.display(
        description=_("Source data deleted at"),
        ordering="from_data_deleted_at",
    )
    def from_data_deleted_at_display(self, obj: LifecycleOperation) -> datetime | None:
        return obj.from_data_deleted_at

    @admin.display(description=_("Source data deletion error"))
    def from_data_deletion_error_display(self, obj: LifecycleOperation) -> str | None:
        return obj.from_data_deletion_error

    @admin.display(description=_("Error message"))
    def error_message_display(self, obj: LifecycleOperation) -> str | None:
        return obj.error_message

    @admin.display(description=_("Bytes moved"))
    def bytes_progress(self, obj: LifecycleOperation) -> str:
        return self._format_bytes_progress(obj.bytes_copied, obj.bytes_total)

    @admin.display(description=_("Files moved"))
    def files_progress(self, obj: LifecycleOperation) -> str:
        return self._format_progress(obj.files_copied, obj.files_total)

    @staticmethod
    def _format_progress(copied: int | None, total: int | None) -> str:
        copied_display = str(copied) if copied is not None else "-"
        total_display = str(total) if total is not None else "-"
        if copied is None or not total:
            return f"{copied_display} / {total_display}"
        percentage = round((copied / total) * 100)
        return f"{copied_display} / {total_display} ({percentage}%)"

    @staticmethod
    def _format_bytes_progress(copied: int | None, total: int | None) -> str:
        copied_display = LifecycleOperationAdmin._format_bytes(copied)
        total_display = LifecycleOperationAdmin._format_bytes(total)
        if copied is None or not total:
            return f"{copied_display} / {total_display}"
        percentage = round((copied / total) * 100)
        return f"{copied_display} / {total_display} ({percentage}%)"

    @staticmethod
    def _format_bytes(value: int | None) -> str:
        if value is None:
            return "-"
        return filesizeformat(value)

    @admin.display(description=_("Error details"))
    def formatted_error_details(self, obj: LifecycleOperation) -> str | None:
        if not obj.error_details:
            return None
        return format_html("<pre>{}</pre>", obj.error_details)
