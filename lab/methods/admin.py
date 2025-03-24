from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import AnalysisMethod, DetectorType, FilterOption, FilterSet


class DetectorInline(admin.TabularInline):
    model = DetectorType
    extra = 0
    fields = ('name', 'field_name', 'is_other_field', 'is_enabled')


class FilterOptionInline(admin.TabularInline):
    model = FilterOption
    extra = 0
    fields = ('name', 'is_enabled')


@admin.register(AnalysisMethod)
class AnalysisMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'field_name', 'description', 'is_enabled', 'detector_count')
    list_filter = ('is_enabled',)
    search_fields = ('name', 'description', 'field_name')
    inlines = [DetectorInline]
    
    def detector_count(self, obj):
        return obj.detectors.count()
    detector_count.short_description = _("Detectors")


@admin.register(DetectorType)
class DetectorTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'field_name', 'is_other_field', 'is_enabled', 'filter_count')
    list_filter = ('method', 'is_enabled', 'is_other_field')
    search_fields = ('name', 'field_name', 'method__name')
    inlines = [FilterOptionInline]
    
    def filter_count(self, obj):
        return obj.filter_options.count()
    filter_count.short_description = _("Filters")


@admin.register(FilterSet)
class FilterSetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'field_name', 'detector')
    search_fields = ('field_name', 'detector__name', 'detector__method__name')