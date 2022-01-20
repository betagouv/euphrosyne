from typing import Any, List, Optional, Tuple, Type, Union

from django.contrib import admin
from django.contrib.admin import ModelAdmin, widgets
from django.contrib.admin.options import InlineModelAdmin
from django.db.models.query import QuerySet
from django.forms.widgets import Select
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from ..fields import ObjectGroupChoiceField
from ..forms import RunDetailsForm
from ..models import Project, Run
from ..permissions import LabRole, get_user_permission_group, is_lab_admin
from .mixins import LabPermission, LabPermissionMixin


class ObjectGroupInline(admin.TabularInline):
    parent_instance: Run
    model = Run.run_object_groups.through
    verbose_name = _("Object group")
    verbose_name_plural = _("Object groups")
    extra = 0

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return True

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return False

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return True

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return True

    def formfield_callback(self, field, **kwargs):
        if field.name == "objectgroup":
            # pylint: disable=no-member
            return ObjectGroupChoiceField(
                project_id=self.parent_instance.project_id,
                widget=widgets.RelatedFieldWidgetWrapper(
                    Select(),
                    Run.run_object_groups.rel,
                    admin_site=self.admin_site,
                    can_add_related=True,
                ),
            )
        return field.formfield(**kwargs)

    def get_formset(self, request: Any, obj: Optional[Run] = None, **kwargs: Any):
        return super().get_formset(
            request, obj=obj, formfield_callback=self.formfield_callback, **kwargs
        )


@admin.register(Run)
class RunAdmin(LabPermissionMixin, ModelAdmin):
    class Media:
        js = ("js/admin/methods.js",)
        css = {"all": ("css/admin/methods.css",)}

    HIDE_ADD_SIDEBAR = True

    form = RunDetailsForm
    list_display = ("project", "label", "start_date", "end_date")
    readonly_fields = ("status",)
    fieldsets = (
        (_("Project"), {"fields": ("project",)}),
        (
            None,
            {"fields": ("label", "status", "start_date", "end_date", "embargo_date")},
        ),
        (
            _("Experimental conditions"),
            {"fields": ("particle_type", "energy_in_keV", "beamline")},
        ),
        (
            "METHODS",
            {
                "fields": (
                    *[f.name for f in Run.get_method_fields()],
                    *[f.name for f in Run.get_detector_fields()],
                    *[f.name for f in Run.get_filters_fields()],
                )
            },
        ),
    )
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
            not obj or obj.status == Run.Status.NEW
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return super().has_delete_permission(request, obj) and (
            not obj or obj.status == Run.Status.NEW
        )

    def has_module_permission(self, request: HttpRequest) -> bool:
        return is_lab_admin(request.user)

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> Union[List[str], Tuple]:
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            readonly_fields += ("project",)
            if (
                obj.project
                and get_user_permission_group(request, obj.project) < LabRole.LAB_ADMIN
            ):
                readonly_fields += ("start_date", "end_date")

        return readonly_fields

    def get_inlines(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> List[Type[InlineModelAdmin]]:
        if obj:
            return [ObjectGroupInline]
        return []

    def get_inline_instances(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> List[InlineModelAdmin]:
        inlines = super().get_inline_instances(request, obj=obj)
        if obj:
            for inline in inlines:
                if isinstance(inline, ObjectGroupInline):
                    inline.parent_instance = obj
        return inlines

    def get_queryset(self, request: HttpRequest):
        runs_queryset = super().get_queryset(request)
        if is_lab_admin(request.user):
            return runs_queryset
        return runs_queryset.filter(project__members__id=request.user.id).distinct()

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self, db_field, request: HttpRequest, queryset: QuerySet[Run] = None, **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "project":
            queryset = Project.objects.filter(
                participation__user_id=request.user.id,
                participation__is_leader=True,
            )

        if queryset is not None:
            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
