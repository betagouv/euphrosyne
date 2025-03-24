"""
Dynamic model generation for ConfigurableMethodModel.

This module is responsible for creating a concrete implementation of the 
ConfigurableMethodModel with fields based on the database configuration.

It should only be imported by the Django migration system or the management command.
"""

from django.apps import apps
from django.conf import settings
from django.db import connection

from .models import (
    AnalysisMethod,
    DetectorType,
    FilterSet,
    Method, 
    Detector,
    Filter,
    OTHER_VALUE,
    MethodBooleanField,
    DetectorBooleanField,
    DetectorCharField,
    FiltersCharField,
    build_dynamic_method_model,
)


def get_dynamic_fields_for_migration():
    """
    Returns a dictionary of fields for use in a migration.
    
    This function is designed to be called during migration to generate
    the fields for the ConfigurableMethodModel based on the current
    database configuration.
    """
    # Check if the database tables exist
    tables_exist = check_if_tables_exist()
    if not tables_exist:
        # Return empty fields if tables don't exist yet
        return {}
    
    # Load models if they're not already loaded
    AnalysisMethod = apps.get_model('lab.methods', 'AnalysisMethod')
    DetectorType = apps.get_model('lab.methods', 'DetectorType')
    FilterSet = apps.get_model('lab.methods', 'FilterSet')
    
    fields = {}
    
    # Add method fields
    for method in AnalysisMethod.objects.filter(is_enabled=True):
        fields[method.field_name] = MethodBooleanField(Method(method.name))
    
    # Add detector fields
    for detector in DetectorType.objects.filter(is_enabled=True, method__is_enabled=True):
        if detector.is_other_field:
            fields[detector.field_name] = DetectorCharField(
                Method(detector.method.name), 
                Detector(OTHER_VALUE)
            )
        else:
            fields[detector.field_name] = DetectorBooleanField(
                Method(detector.method.name), 
                Detector(detector.name)
            )
    
    # Add filter fields
    for filter_set in FilterSet.objects.filter(detector__is_enabled=True, detector__method__is_enabled=True):
        filter_options = list(filter_set.filter_options.all())
        if filter_options:
            filter_values = [Filter(option.name) for option in filter_options]
            # Always add an "other" option
            if not any(f.value == OTHER_VALUE for f in filter_values):
                filter_values.append(Filter(OTHER_VALUE))
            
            fields[filter_set.field_name] = FiltersCharField(
                Method(filter_set.detector.method.name),
                Detector(filter_set.detector.name),
                filter_values
            )
    
    return fields


def check_if_tables_exist():
    """Check if the necessary tables exist in the database."""
    with connection.cursor() as cursor:
        tables = connection.introspection.table_names()
        
        # Check for our configuration tables
        required_tables = [
            f"{connection.ops.quote_name('lab_methods_analysismethod')}",
            f"{connection.ops.quote_name('lab_methods_detectortype')}",
            f"{connection.ops.quote_name('lab_methods_filterset')}"
        ]
        
        for table in required_tables:
            if table.lower() not in [t.lower() for t in tables]:
                return False
                
    return True