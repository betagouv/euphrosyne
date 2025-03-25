from typing import Literal, Optional

from django.conf import settings
from django.contrib.admin.helpers import AdminField, AdminForm
from django.utils.module_loading import import_string

from lab.runs.models import Run

from .dto import MethodDTO, method_model_to_dto

LabMethodModel = import_string(settings.METHOD_MODEL_CLASS)


def _get_adminfield_name(admin_field: AdminField) -> str:
    return str(
        admin_field.field["name"]
        if isinstance(admin_field.field, dict)
        else admin_field.field.name
    )


def _get_adminfields(adminform: AdminForm, select: list[str]) -> list[AdminField]:
    """Get fields from an AdminForm based on a selected list of field names

    `select` must be ordered.
    """
    all_fields: dict[str, AdminField] = {
        _get_adminfield_name(admin_field): admin_field  # type: ignore
        for fieldset in adminform
        for line in fieldset
        for admin_field in line
    }
    return [all_fields[fieldname] for fieldname in select]


def method_fields(adminform: AdminForm) -> list[AdminField]:
    return _get_adminfields(
        adminform, [f.name for f in LabMethodModel.get_method_fields()]
    )


def detector_fields(adminform: AdminForm, method_fieldname: str) -> list[AdminField]:
    detector_fieldnames = [
        detector_field.name
        for detector_field in LabMethodModel.get_detector_fields()
        if LabMethodModel.get_method_field(detector_field.method).name
        == method_fieldname
    ]
    return _get_adminfields(adminform, detector_fieldnames)


def filters_field(
    adminform: AdminForm, detector_fieldname: str
) -> Optional[AdminField]:
    detector_modelfield = getattr(LabMethodModel, detector_fieldname).field
    filters_modelfield = LabMethodModel.get_filters_field(
        detector_modelfield.method, detector_modelfield.detector
    )
    if filters_modelfield:
        return _get_adminfields(adminform, [filters_modelfield.name])[0]
    return None


def run_methods_repr(run: Run) -> dict[Literal["methods"], list[MethodDTO]]:
    return {"methods": method_model_to_dto(run)}
