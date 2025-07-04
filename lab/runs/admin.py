from typing import Any

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from euphro_tools.hooks import initialize_run_directory, rename_run_directory
from lab.admin.mixins import LabPermission, LabPermissionMixin
from lab.permissions import LabRole, is_lab_admin
from lab.projects.models import Project

from .admin_actions import change_state
from .forms import (
    RunCreateAdminForm,
    RunCreateForm,
    RunDetailsAdminForm,
    RunDetailsForm,
    RunScheduleForm,
)
from .models import Run
from .signals import run_scheduled


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
        css = {
            "all": (
                "css/admin/methods.css",
                "css/admin/run.css",
            )
        }

    HIDE_ADD_SIDEBAR = True
    actions = [change_state]
    list_filter = ("project",)

    lab_permissions = LabPermission(
        add_permission=LabRole.ANY_STAFF_USER,
        view_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.LAB_ADMIN,
    )

    def get_related_project(  # type: ignore[override]
        self, obj: Run | None = None
    ) -> Project | None:
        if obj:
            return obj.project
        return None

    def has_change_permission(
        self, request: HttpRequest, obj: Run | None = None  # type: ignore[override]
    ) -> bool:
        if is_lab_admin(request.user):
            return True
        return super().has_change_permission(request, obj) and (
            not obj or obj.status == Run.Status.CREATED
        )

    def has_module_permission(self, request: HttpRequest) -> bool:
        return False

    def get_form(
        self,
        request: HttpRequest,
        obj: Run | None = None,
        change: bool = False,
        **kwargs
    ):
        if is_lab_admin(request.user):
            if obj:
                return RunDetailsAdminForm
            return RunCreateAdminForm
        if obj:
            return RunDetailsForm
        return RunCreateForm

    def get_fieldsets(self, request: HttpRequest, obj: Run | None = None):
        fieldset_classes = [
            "fr-mb-0",
            "fr-pb-1w",
            "flex-container",
            "flex-flow--wrap",
        ]
        fieldsets = []

        member_basic_info_fields = ["label"]
        admin_basic_info_fields = [*member_basic_info_fields, "embargo_date"]
        if not obj:
            fieldsets += [
                (
                    str(_("Basic information")),
                    {
                        "fields": (
                            admin_basic_info_fields
                            if is_lab_admin(request.user)
                            else member_basic_info_fields
                        )
                    },
                )
            ]
        else:
            if is_lab_admin(request.user):
                fieldsets += [
                    (
                        str(_("Basic information")),
                        {
                            "fields": ["label"],
                            "classes": [*fieldset_classes],
                        },
                    )
                ]
            fieldsets += [
                (
                    str(_("Experimental conditions")),
                    {
                        "fields": ["particle_type", "energy_in_keV", "beamline"],
                        "classes": [*fieldset_classes],
                    },
                ),
                (
                    "METHODS",
                    {
                        "fields": [
                            *[f.name for f in Run.get_method_fields()],
                            *[f.name for f in Run.get_detector_fields()],
                            *[f.name for f in Run.get_filters_fields()],
                        ]
                    },
                ),
            ]

        return fieldsets

    def get_changelist(self, request, **kwargs):
        return RunChangeList

    def get_queryset(self, request: HttpRequest):
        runs_queryset = super().get_queryset(request)
        if is_lab_admin(request.user):
            return runs_queryset
        return runs_queryset.filter(project__members__id=request.user.id).distinct()

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self, db_field, request: HttpRequest, queryset: QuerySet | None = None, **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "project":
            queryset = Project.objects.filter(
                participation__user_id=request.user.id,  # type: ignore[misc]
            )

        if queryset is not None:
            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        project = self._get_project(request, object_id)
        if not project:
            self.message_user(
                request,
                _(
                    "You do not have permission for this project. "
                    "If you think this is an error, please contact the New AGLAE team."
                ),
                messages.WARNING,
            )
            return redirect(reverse("admin:lab_project_changelist"))
        is_popup = "_popup" in request.GET
        extra_context = {
            **(extra_context if extra_context else {}),
            "show_save_as_new": False,
            "show_save_and_add_another": False,
            "show_save": is_popup,
            "project": project,
        }

        if request.method == "POST" and request.POST.get("_action") == "schedule_run":
            schedule_form = self._schedule_action(
                request,
                obj=self.get_object(request, object_id),
            )
            request.method = "GET"  # treat as a GET request to display the form again
        else:
            schedule_form = RunScheduleForm(
                instance=self.get_object(request, object_id),
            )

        if object_id is not None:
            extra_context["schedule_modal"] = {
                "id": "schedule-modal",
                "form": schedule_form,
            }

        return super().changeform_view(request, object_id, form_url, extra_context)

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, str] | None = None
    ):
        project = self._get_project(request)
        return super().changelist_view(
            request,
            {
                **(extra_context if extra_context else {}),
                "project": project,
            },
        )

    def save_form(self, request: HttpRequest, form: ModelForm, change: bool):
        if not change:
            form.instance.project = self._get_project(request, form.instance.id)
        return super().save_form(request, form, change)

    def save_model(self, request: Any, obj: Run, form: ModelForm, change: bool) -> None:
        super().save_model(request, obj, form, change)
        if not change:
            initialize_run_directory(obj.project.name, obj.label)
        elif "label" in form.changed_data:
            rename_run_directory(obj.project.name, form.initial["label"], obj.label)

    def _get_project(self, request, object_id=None) -> Project | None:
        if object_id:
            run = self.get_object(request, object_id)
            if not run:
                return None
            return run.project
        if "project" in request.GET:
            qs = Project.objects.filter(id=request.GET["project"])
            if not is_lab_admin(request.user):
                qs = qs.filter(members__id=request.user.id)
            return qs.first()
        return None

    def _schedule_action(self, request: HttpRequest, obj: Run):
        schedule_form = RunScheduleForm(
            data=request.POST,
            files=request.FILES,
            instance=obj,
        )
        if not is_lab_admin(request.user):
            raise PermissionDenied
        was_run_scheduled = obj.start_date
        if schedule_form.is_valid():
            new_object = self.save_form(request, schedule_form, change=True)
            self.save_model(request, new_object, schedule_form, True)
            if new_object.start_date and not was_run_scheduled:
                run_scheduled.send(self.__class__, instance=new_object)
        return schedule_form
