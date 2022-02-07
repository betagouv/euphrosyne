import datetime
import json
import locale
from datetime import time
from typing import Any, List, Optional, Tuple, Type, Union

from django.contrib import admin
from django.contrib.admin import ModelAdmin, widgets
from django.contrib.admin.options import IS_POPUP_VAR, InlineModelAdmin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.template.response import TemplateResponse
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from ..fields import ObjectGroupChoiceField
from ..forms import RunDetailsForm
from ..models import Project, Run
from ..permissions import LabRole, is_lab_admin
from ..widgets import PlaceholderSelect, SplitDateTimeWithDefaultTime
from .mixins import LabPermission, LabPermissionMixin


class ObjectGroupInline(admin.TabularInline):
    template = "admin/edit_inline/tabular_objectgroup_in_run.html"
    parent_instance: Run
    model = Run.run_object_groups.through
    verbose_name = _("Batch of objects")
    verbose_name_plural = _("Batches of objects")
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
                    PlaceholderSelect(),
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
            _("Basic information"),
            {"fields": ("label", "status", "start_date", "end_date")},
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

        if not is_lab_admin(request.user):
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
        project = None
        if object_id:
            project = self.get_object(request, object_id).project
        elif "project" in request.GET:
            project = Project.objects.get(id=request.GET["project"])
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
                "force_hide_close": True,
                "project": project,
            },
        )

    @staticmethod
    def _serialized_data(request, obj):
        current_locale = (translation.to_locale(request.LANGUAGE_CODE), "UTF-8")
        locale.setlocale(locale.LC_ALL, locale=current_locale)

        fieldnames = [
            "id",
            "label",
            "start_date",
            "end_date",
            "particle_type",
            "energy_in_keV",
            "beamline",
        ]

        def _serialize(field_name):
            field = getattr(obj, field_name)
            if isinstance(field, datetime.datetime):
                return field.strftime("%d %B %Y %H:%S")
            return str(field)

        return {
            field.name: _serialize(field.name)
            for field in obj._meta.get_fields()
            if field.name in fieldnames
        }

    def response_add(self, request, obj, post_url_continue=None):
        if IS_POPUP_VAR in request.POST:
            popup_response_data = json.dumps(
                {
                    "action": "add",
                    "data": self._serialized_data(request, obj),
                }
            )
            return TemplateResponse(
                request,
                "admin/run_popup_response.html",
                {
                    "popup_response_data": popup_response_data,
                },
            )

        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if IS_POPUP_VAR in request.POST:
            popup_response_data = json.dumps(
                {
                    "action": "change",
                    "data": self._serialized_data(request, obj),
                }
            )
            return TemplateResponse(
                request,
                "admin/run_popup_response.html",
                {
                    "popup_response_data": popup_response_data,
                },
            )
        return super().response_change(request, obj)

    def response_delete(self, request, obj_display, obj_id):
        if IS_POPUP_VAR in request.POST:
            popup_response_data = json.dumps({"action": "delete", "id": obj_id})
            return TemplateResponse(
                request,
                "admin/run_popup_response.html",
                {
                    "popup_response_data": popup_response_data,
                },
            )

        return super().response_delete(request, obj_display, obj_id)
