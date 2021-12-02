import pytest

from ..model_fields import (
    DetectorBooleanField,
    DetectorCharField,
    FiltersCharField,
    MethodBooleanField,
)
from ..models import MethodModel


def test_methods_are_distinct():
    assert len(set(f.method for f in MethodModel.get_method_fields())) == len(
        MethodModel.get_method_fields()
    )


def test_detectors_are_distinct_per_method():
    assert len(
        set((f.method, f.detector) for f in MethodModel.get_detector_fields())
    ) == len(MethodModel.get_detector_fields())


def test_filters_are_distinct_per_detector():
    assert len(
        set((f.method, f.detector) for f in MethodModel.get_filters_fields())
    ) == len(MethodModel.get_filters_fields())


@pytest.mark.parametrize("filters_field", MethodModel.get_filters_fields())
def test_each_filters_choice_is_distinct(filters_field):
    assert len(set(filters_field.filters)) == len(filters_field.filters)


@pytest.mark.parametrize("method", [f.method for f in MethodModel.get_method_fields()])
def test_get_method_field_always_return(method):
    assert isinstance(MethodModel.get_method_field(method), MethodBooleanField)


@pytest.mark.parametrize(
    "method_detector",
    [(f.method, f.detector) for f in MethodModel.get_detector_fields()],
)
def test_get_detector_field_always_return(method_detector):
    assert isinstance(
        MethodModel.get_detector_field(*method_detector),
        (DetectorBooleanField, DetectorCharField),
    )


@pytest.mark.parametrize(
    "method_detector",
    [(f.method, f.detector) for f in MethodModel.get_filters_fields()],
)
def test_get_filters_field_always_return(method_detector):
    assert isinstance(MethodModel.get_filters_field(*method_detector), FiltersCharField)


@pytest.mark.parametrize(
    "method_detector",
    [(f.method, f.detector) for f in MethodModel.get_detector_fields()],
)
def test_get_filters_field_maybe_returns_for_detectors(method_detector):
    assert isinstance(
        MethodModel.get_filters_field(*method_detector), (type(None), FiltersCharField)
    )
