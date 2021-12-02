from typing import Optional

from django.contrib.admin.helpers import AdminField, AdminForm

from .models import MethodModel


def _get_adminfield_name(admin_field: AdminField) -> str:
    return (
        admin_field.field["name"]
        if isinstance(admin_field.field, dict)
        else admin_field.field.name
    )


def _get_adminfields(
    adminform: AdminForm, select: list[str] = None
) -> list[AdminField]:
    """Get fields from an AdminForm based on a selected list of field names

    `select` must be ordered.
    """
    all_fields = {
        _get_adminfield_name(admin_field): admin_field
        for fieldset in adminform
        for line in fieldset
        for admin_field in line
    }
    return [all_fields[fieldname] for fieldname in select]


def method_fields(adminform: AdminForm) -> list[AdminField]:
    return _get_adminfields(
        adminform, [f.name for f in MethodModel.get_method_fields()]
    )


def detector_fields(adminform: AdminForm, method_fieldname: str) -> list[AdminField]:
    detector_fieldnames = [
        detector_field.name
        for detector_field in MethodModel.get_detector_fields()
        if MethodModel.get_method_field(detector_field.method).name == method_fieldname
    ]
    return _get_adminfields(adminform, detector_fieldnames)


def filters_field(
    adminform: AdminForm, detector_fieldname: str
) -> Optional[AdminField]:
    detector_modelfield = getattr(MethodModel, detector_fieldname).field
    filters_modelfield = MethodModel.get_filters_field(
        detector_modelfield.method, detector_modelfield.detector
    )
    if filters_modelfield:
        return _get_adminfields(adminform, [filters_modelfield.name])[0]
    return None
