from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import yaml
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from ..forms import build_detector_used_inline_form
from ..models import AnalysisTechniqueUsed, DetectorUsed, Project, Run
from ..permissions import is_lab_admin
from .mixins import LabPermission, LabPermissionMixin, LabRole

# [XXX] Wrap in a service
with open(Path(__file__).parent.parent / "models" / "run-choices-config.yaml") as f:
    RUN_CHOICES = yaml.safe_load(f.read())


@admin.register(DetectorUsed)
class DetectorUsedAdmin(LabPermissionMixin, ModelAdmin):
    model = DetectorUsed

    # [XXX] No good way to get the filter for now
    def get_form(
        self, request: Any, obj: Optional[Any] = ..., change: bool = ..., **kwargs: Any
    ):
        analysis_technique_used_id = request.GET.get("analysis_technique_used")
        choices = None
        if analysis_technique_used_id:
            try:
                analysis_technique_used = AnalysisTechniqueUsed.objects.select_related(
                    "run"
                ).get(pk=analysis_technique_used_id)
            except AnalysisTechniqueUsed.DoesNotExist:
                pass
            run = analysis_technique_used.run
            beamline = run.beamline
            try:
                choices = (
                    RUN_CHOICES["beamlines"][beamline]
                    .get("analysis_techniques", dict())
                    .get(analysis_technique_used.label)
                    .get("detectors")
                    .keys()
                )
            except KeyError:
                pass
        return build_detector_used_inline_form(choices=choices)

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(
        self, obj: Optional[DetectorUsed] = None
    ) -> Optional[Project]:
        if obj and obj.analysis_technique_used and obj.analysis_technique_used.run:
            return obj.analysis_techniques_used.run.project
        return None

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[DetectorUsed] = None
    ) -> bool:
        return super().has_change_permission(request, obj) and (
            not obj
            or not obj.analysis_technique_used
            or not obj.analysis_technique_used.run
            or obj.analysis_technique_used.run.status == Run.Status.NOT_STARTED
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[DetectorUsed] = None
    ) -> bool:
        return super().has_delete_permission(request, obj) and (
            not obj
            or not obj.analysis_technique_used
            or not obj.analysis_technique_used.run
            or obj.analysis_technique_used.run.status == Run.Status.NOT_STARTED
        )

    def has_module_permission(self, request: HttpRequest) -> bool:
        return is_lab_admin(request.user)

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[DetectorUsed] = None
    ) -> Union[List[str], Tuple]:
        if obj:
            return super().get_readonly_fields(request, obj) + (
                "analysis_technique_used",
            )
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request: HttpRequest):
        runs_queryset = super().get_queryset(request)
        if is_lab_admin(request.user):
            return runs_queryset
        return runs_queryset.filter(
            analysis_technique_used__run__project__members__id=request.user.id
        )

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self,
        db_field,
        request: HttpRequest,
        queryset: QuerySet[DetectorUsed] = None,
        **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "run":
            queryset = AnalysisTechniqueUsed.objects.filter(
                run__project__participation__user_id=request.user.id,
            )

        # [XXX] Write non-reg test for this
        if queryset is not None:
            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
