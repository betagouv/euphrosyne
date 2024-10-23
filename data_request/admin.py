from django.contrib import admin, messages
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from euphro_tools.exceptions import EuphroToolsException
from lab.admin.mixins import LabAdminAllowedMixin
from lab.permissions import is_lab_admin

from .data_links import send_links
from .models import DataAccessEvent, DataRequest


class ReadonlyInlineMixin:

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: Model | None = None,  # pylint: disable=unused-argument
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: Model | None = None,  # pylint: disable=unused-argument
    ) -> bool:
        return is_lab_admin(request.user)

    def has_add_permission(
        self,
        request: HttpRequest,
        obj: Model | None = None,  # pylint: disable=unused-argument
    ) -> bool:
        return False

    def has_view_permission(
        self,
        request: HttpRequest,
        obj: Model | None = None,  # pylint: disable=unused-argument
    ) -> bool:
        return is_lab_admin(request.user)


@admin.action(description=_("Accept request(s) (send download links)"))
def action_send_links(
    # pylint: disable=unused-argument
    modeladmin: "DataRequestAdmin",
    request: HttpRequest,
    queryset: QuerySet[DataRequest],
):
    for data_request in queryset:
        try:
            send_links(data_request)
        except EuphroToolsException as error:
            modeladmin.message_user(
                request,
                _("Error sending links to %(email)s for %(data_request)s: %(error)s")
                % {
                    "data_request": data_request,
                    "error": error,
                    "email": data_request.user_email,
                },
                level=messages.ERROR,
            )
            continue
        data_request.sent_at = timezone.now()
        if not data_request.request_viewed:
            data_request.request_viewed = True
        data_request.save()


class BeenSeenListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("has been sent")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "been_sent"

    def lookups(self, request, model_admin):
        return [
            ("1", _("Yes")),
            ("0", _("No")),
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet[DataRequest]):
        if not self.value():
            return queryset
        return queryset.filter(sent_at__isnull=self.value() == "0")


class DataAccessEventInline(ReadonlyInlineMixin, admin.TabularInline):
    model = DataAccessEvent
    extra = 0

    fields = ("path", "access_time")
    readonly_fields = ("path", "access_time")


class RunInline(ReadonlyInlineMixin, admin.TabularInline):
    model = DataRequest.runs.through
    verbose_name = "Run"
    verbose_name_plural = "Runs"
    extra = 0

    fields = ("run",)


@admin.register(DataRequest)
class DataRequestAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    actions = [action_send_links]
    list_filter = [BeenSeenListFilter]

    list_display = (
        "created",
        "sent_at",
        "user_email",
        "user_first_name",
        "user_last_name",
        "display_viewed",
    )

    fields = (
        "created",
        "sent_at",
        "user_email",
        "user_first_name",
        "user_last_name",
        "user_institution",
        "description",
    )
    readonly_fields = (
        "created",
        "user_email",
        "user_first_name",
        "user_last_name",
        "user_institution",
        "description",
    )

    inlines = [RunInline, DataAccessEventInline]

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None):
        return False

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, bool] | None = None,
    ) -> HttpResponse:
        obj = self.get_object(request, object_id)
        if obj and not obj.request_viewed:
            obj.request_viewed = True
            obj.save()
        response = super().change_view(request, object_id, form_url, extra_context)
        return response

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, str] | None = None
    ):
        extra_context = extra_context or {}
        extra_context["title"] = gettext("Data requests")
        return super().changelist_view(request, extra_context)

    @admin.display(description=_("Is sent"), boolean=True)
    def is_sent(self, obj: "DataRequest") -> bool:
        return obj.sent_at is not None

    @admin.display(description="")
    def display_viewed(self, obj: "DataRequest") -> str:
        if obj.request_viewed:
            return ""
        return mark_safe(
            f'<p class="fr-badge fr-badge--new fr-badge--sm">{_("New")}</p>'
        )
