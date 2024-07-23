from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext

from lab.runs.models import Run

from .models import Project


class ProjectStatusListFilter(admin.SimpleListFilter):
    title = _("run status")

    parameter_name = "run_status"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return [
            (enum_member.name, enum_member.value[1])
            for enum_member in list(Project.Status)
            if enum_member != Project.Status.TO_SCHEDULE
            # exclude TO_SCHEDULE from filter as it is displayed in a separate table
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter_by_status(Project.Status[self.value()])
        return queryset


class ProjectRunActiveEmbargoFilter(admin.SimpleListFilter):
    class FiterValues:
        EMBARGO_ACTIVE = "embargo_active"
        EMBARGO_OVER = "embargo_over"
        EMBARGO_NONE = "embargo_none"
        CONFIDENTIAL = "confidential"

    title = _("data status")

    parameter_name = "data_status"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return [
            (self.FiterValues.EMBARGO_OVER, _("Available (DIGILAB)")),
            (self.FiterValues.EMBARGO_ACTIVE, _("Available (FIXLAB)")),
            (self.FiterValues.EMBARGO_NONE, _("Hidden (DIGILAB)")),
            (self.FiterValues.CONFIDENTIAL, pgettext("for data", "Confidential")),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        if value == self.FiterValues.EMBARGO_ACTIVE:
            runs = Run.objects.filter(embargo_date__gte=timezone.now())
            return queryset.filter(runs__in=runs)
        if value == self.FiterValues.EMBARGO_OVER:
            runs = Run.objects.filter(embargo_date__lt=timezone.now())
            return queryset.filter(runs__in=runs)
        if value == self.FiterValues.EMBARGO_NONE:
            return queryset.filter(runs__embargo_date__isnull=True)
        if value == self.FiterValues.CONFIDENTIAL:
            return queryset.filter(confidential=True)
        return queryset
