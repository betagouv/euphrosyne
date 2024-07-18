from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from lab.runs.models import Run

from .models import Project


class ProjectStatusListFilter(admin.SimpleListFilter):
    title = _("status")

    parameter_name = "status"
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
    title = _("embargo status")

    parameter_name = "embargo"
    template = "admin/lab/project/filter.html"

    def lookups(self, request, model_admin):
        return [("active", _("Active")), ("over", _("Over")), ("none", _("Not set"))]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "active":
                runs = Run.objects.filter(embargo_date__gte=timezone.now())
                return queryset.filter(runs__in=runs)
            if self.value() == "over":
                runs = Run.objects.filter(embargo_date__lt=timezone.now())
                return queryset.filter(runs__in=runs)
            if self.value() == "none":
                return queryset.filter(runs__embargo_date__isnull=True)
        return queryset
