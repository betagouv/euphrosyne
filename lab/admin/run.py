from datetime import time
from typing import Any, List, Optional, Tuple, Type, Union

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from euphro_tools.hooks import initialize_run_directory, rename_run_directory

from ..forms import RunDetailsForm
from ..models import Project, Run
from ..objects.fields import ObjectGroupChoiceField
from ..permissions import LabRole, is_lab_admin
from ..widgets import RelatedObjectRunWidgetWrapper, SplitDateTimeWithDefaultTime
from .mixins import LabPermission, LabPermissionMixin
from .run_actions import change_state


class ObjectGroupInline(admin.TabularInline):
    template = "admin/edit_inline/tabular_objectgroup_in_run.html"
    parent_instance: Run
    model = Run.run_object_groups.through
    verbose_name = _("Object / Sample")
    verbose_name_plural = _("Object(s) / Sample(s)")
    extra = 0

    class Media:
        js = ("pages/objectgroup-inline.js",)

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
                widget=RelatedObjectRunWidgetWrapper(
                    self.parent_instance,
                    admin_site=self.admin_site,
                    can_add_related=True,
                ),
            )
        return field.formfield(**kwargs)

    def get_formset(self, request: Any, obj: Optional[Run] = None, **kwargs: Any):
        return super().get_formset(
            request, obj=obj, formfield_callback=self.formfield_callback, **kwargs
        )


class RunChangeList(ChangeList):
    def get_queryset(self, request, exclude_parameters=None):
        remaining_lookup_params = self.get_filters(request)[2]
        if "project" in remaining_lookup_params and not (
            is_lab_admin(request.user)
            or Project.objects.filter(
                id=remaining_lookup_params["project"][0], members__id=request.user.id
            ).exists()
        ):
            raise PermissionDenied
        return super().get_queryset(request, exclude_parameters=exclude_parameters)


@admin.register(Run)
class RunAdmin(LabPermissionMixin, ModelAdmin):
    class Media:
        js = ("pages/run.js",)
        css = {
            "all": (
                "css/admin/methods.css",
                "css/admin/run.css",
            )
        }

    HIDE_ADD_SIDEBAR = True
    form = RunDetailsForm
    actions = [change_state]
    list_filter = ("project",)
    fieldsets = (
        (_("Project"), {"fields": ("project",)}),
        (
            _("Basic information"),
            {"fields": ("label", "status", "start_date", "end_date")},
        ),
        (
            _("Experimental conditions"),
            {
                "fields": ("particle_type", "energy_in_keV", "beamline"),
                "classes": ("mb-0",),
            },
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
            not obj or obj.status == Run.Status.CREATED
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> bool:
        return super().has_delete_permission(request, obj) and (
            not obj or obj.status == Run.Status.CREATED
        )

    def has_module_permission(self, request: HttpRequest) -> bool:
        return False

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[Run] = None
    ) -> Union[List[str], Tuple]:
        readonly_fields = (*super().get_readonly_fields(request, obj), "status")
        if obj:
            # Prevent changing label after creation (because of data folder sync).
            readonly_fields += ("project",)

        if not is_lab_admin(request.user):
            readonly_fields += ("start_date", "end_date")

        return readonly_fields

    def get_changelist(self, request, **kwargs):
        return RunChangeList

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

    def formfield_for_dbfield(  # pylint: disable=arguments-differ
        self, db_field, request: HttpRequest, **kwargs
    ):
        # Widget edit here because form fields are overriden by admin
        # & SplitDateTimeWithDefaultTime is an admin widget and cannot be used directly
        # in a ModelForm (it returns a 2-n list as value instead of a 1-n list).
        if db_field.name == "start_date":
            kwargs["widget"] = SplitDateTimeWithDefaultTime(default_time_value=time(9))
        if db_field.name == "end_date":
            kwargs["widget"] = SplitDateTimeWithDefaultTime(default_time_value=time(18))
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self, db_field, request: HttpRequest, queryset: QuerySet[Run] = None, **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "project":
            queryset = Project.objects.filter(
                participation__user_id=request.user.id,
            )

        if queryset is not None:
            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        project = self._get_project(request, object_id)
        is_popup = "_popup" in request.GET
        return super().changeform_view(
            request,
            object_id,
            form_url,
            {
                **(extra_context if extra_context else {}),
                "show_save_as_new": False,
                "show_save_and_add_another": False,
                "show_save": is_popup,
                "project": project,
            },
        )

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[dict[str, str]] = None
    ):
        project = self._get_project(request)
        return super().changelist_view(
            request,
            {
                **(extra_context if extra_context else {}),
                "project": project,
            },
        )

    def save_model(self, request: Any, obj: Run, form: ModelForm, change: bool) -> None:
        super().save_model(request, obj, form, change)
        if not change:
            initialize_run_directory(obj.project.name, obj.label)
        elif "label" in form.changed_data:
            rename_run_directory(obj.project.name, form.initial["label"], obj.label)

    def _get_project(self, request, object_id=None) -> Optional[Project]:
        if object_id:
            return self.get_object(request, object_id).project
        if "project" in request.GET:
            return Project.objects.get(id=request.GET["project"])
        return None
