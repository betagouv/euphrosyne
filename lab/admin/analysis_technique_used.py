from typing import List, Optional, Tuple, Union

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from ..forms import AnalysisTechniqueUsedAdminForm
from ..models import AnalysisTechniqueUsed, DetectorUsed, Project, Run
from ..permissions import is_lab_admin
from .mixins import LabPermission, LabPermissionMixin, LabRole


class DetectorsUsedInline(LabPermissionMixin, admin.TabularInline):
    model = DetectorUsed
    extra = 0
    show_change_link = True
    template = "admin/edit_inline/stacked_detector_used_in_analysis.html"

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[AnalysisTechniqueUsed] = None
    ) -> Union[List[str], Tuple]:
        return [f.name for f in DetectorUsed._meta.fields]

    lab_permissions = LabPermission(
        add_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_MEMBER,
        view_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(
        self, obj: Optional[AnalysisTechniqueUsed] = None
    ) -> Optional[Project]:
        if obj and obj.run:
            return obj.run.project
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


@admin.register(AnalysisTechniqueUsed)
class AnalysisTechniqueUsedAdmin(LabPermissionMixin, ModelAdmin):
    model = AnalysisTechniqueUsed
    form = AnalysisTechniqueUsedAdminForm
    inlines = (DetectorsUsedInline,)

    lab_permissions = LabPermission(
        add_permission=LabRole.ANY_STAFF_USER,
        view_permission=LabRole.PROJECT_MEMBER,
        change_permission=LabRole.PROJECT_MEMBER,
        delete_permission=LabRole.PROJECT_MEMBER,
    )

    def get_related_project(
        self, obj: Optional[AnalysisTechniqueUsed] = None
    ) -> Optional[Project]:
        if obj and obj.run:
            return obj.run.project
        return None

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[AnalysisTechniqueUsed] = None
    ) -> bool:
        return super().has_change_permission(request, obj) and (
            not obj or not obj.run or obj.run.status == Run.Status.NOT_STARTED
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[AnalysisTechniqueUsed] = None
    ) -> bool:
        return super().has_delete_permission(request, obj) and (
            not obj or not obj.run or obj.run.status == Run.Status.NOT_STARTED
        )

    def has_module_permission(self, request: HttpRequest) -> bool:
        return is_lab_admin(request.user)

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[AnalysisTechniqueUsed] = None
    ) -> Union[List[str], Tuple]:
        if obj:
            return super().get_readonly_fields(request, obj) + ("run",)
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request: HttpRequest):
        runs_queryset = super().get_queryset(request)
        if is_lab_admin(request.user):
            return runs_queryset
        return runs_queryset.filter(run__project__members__id=request.user.id)

    def formfield_for_foreignkey(  # pylint: disable=arguments-differ
        self,
        db_field,
        request: HttpRequest,
        queryset: QuerySet[AnalysisTechniqueUsed] = None,
        **kwargs
    ):
        if not is_lab_admin(request.user) and db_field.name == "run":
            queryset = Run.objects.filter(
                project__participation__user_id=request.user.id,
            )

        # [XXX] Write non-reg test for this
        if queryset is not None:
            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
