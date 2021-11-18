from typing import List, Optional, Tuple, Union

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _

from ..forms import RunDetailsForm
from ..models import AnalysisTechniqueUsed, Project, Run
from ..permissions import is_lab_admin
from .mixins import LabPermission, LabPermissionMixin, LabRole


class AnalysisTechniqueUsedInline(LabPermissionMixin, admin.TabularInline):
    model = AnalysisTechniqueUsed
    extra = 0
    show_change_link = True
    template = "admin/edit_inline/stacked_analysis_technique_used_in_run.html"

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> Union[List[str], Tuple]:
        return [f.name for f in AnalysisTechniqueUsed._meta.fields]

    @staticmethod
    @admin.display(description=_("Detectors"))
    def list_detectors_used(
        obj: Optional[AnalysisTechniqueUsed],
    ) -> Optional[str]:
        if obj:
            return format_html_join("\n", "<li>{}</li>", obj.detectors.all())
        return None

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(self, obj: Optional[Run] = None) -> Optional[Project]:
        if obj:
            return obj.project
        return None

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Run] = ...
    ) -> bool:
        """Disable adding a new run through the inline, force the user to go
        through the Run admin page
        """
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Run] = ...
    ) -> bool:
        return False


def load_base_run_fieldsets():
    return (
        (
            None,
            {"fields": ("label", "status", "start_date", "end_date", "embargo_date")},
        ),
        (
            _("Experimental conditions"),
            {"fields": ("particle_type", "energy_in_keV", "beamline")},
        ),
    )


# Allowance: ADMIN:lab admin, EDITOR:project participant
@admin.register(Run)
class RunAdmin(LabPermissionMixin, ModelAdmin):
    form = RunDetailsForm
    list_display = ("project", "label", "start_date", "end_date")
    readonly_fields = ("status",)
    fieldsets = ((_("Project"), {"fields": ("project",)}),) + load_base_run_fieldsets()
    inlines = (AnalysisTechniqueUsedInline,)

    lab_permissions = LabPermission(
        add_permission=LabRole.ANY_STAFF_USER,
        view_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(self, obj: Optional[Run] = None) -> Optional[Project]:
        if obj:
            return obj.project
        return None

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return super().has_change_permission(request, obj) and (
            not obj or obj.status == Run.Status.NOT_STARTED
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return super().has_delete_permission(request, obj) and (
            not obj or obj.status == Run.Status.NOT_STARTED
        )

    def has_module_permission(self, request: HttpRequest) -> bool:
        return is_lab_admin(request.user)

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> Union[List[str], Tuple]:
        if obj:
            return super().get_readonly_fields(request, obj) + ("project",)
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request: HttpRequest):
        runs_queryset = super().get_queryset(request)
        if is_lab_admin(request.user):
            return runs_queryset
        return runs_queryset.filter(project__members__id=request.user.id)

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self, db_field, request: HttpRequest, queryset: QuerySet[Run] = None, **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "project":
            queryset = Project.objects.filter(
                participation__user_id=request.user.id,
            )

        # [XXX] Write non-reg test for this
        if queryset is not None:
            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
