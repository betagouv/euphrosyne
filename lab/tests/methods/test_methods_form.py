from unittest.mock import patch

import pytest
from django.db.models import QuerySet

from ...forms import RunDetailsForm
from ...models import Run
from .. import factories


@pytest.fixture(scope="module", autouse=True)
def patch_queryset_exists():
    with patch.object(QuerySet, "exists", return_value=False) as _fixture:
        yield _fixture


def test_form_validates_no_method():
    form = RunDetailsForm(data={"label": "needed", "beamline": "Microbeam"})
    assert form.is_valid()


@pytest.mark.parametrize("method_field", Run.get_method_fields())
def test_form_validates_method_without_detector(method_field):
    form = RunDetailsForm(
        data={"label": "needed", "beamline": "Microbeam", method_field.name: True}
    )
    assert form.is_valid()


def test_form_validates_mutliple_methods():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "method_PIGE": True,
        }
    )
    assert form.is_valid()


def test_form_validates_mutliple_detectors_over_different_methods():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_LE0": True,
            "method_IBIL": True,
            "detector_IBIL_QE65000": True,
        }
    )
    assert form.is_valid()


def test_form_validates_mutliple_detectors_in_the_same_method():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_LE0": True,
            "detector_HE1": True,
        }
    )
    assert form.is_valid()


def test_form_resets_booleanfield_detector_if_corresponding_method_unselected():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_IBIL": False,
            "detector_IBIL_QE65000": True,
        }
    )
    run = form.save(commit=False)
    assert not run.detector_IBIL_QE65000


def test_form_resets_charfield_detector_if_corresponding_method_unselected():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_ERDA": False,
            "detector_ERDA": "something",
        }
    )
    run = form.save(commit=False)
    assert run.detector_ERDA == ""


def test_form_resets_detector_if_corresponding_method_not_posted():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "detector_IBIL_QE65000": True,
        }
    )
    run = form.save(commit=False)
    assert not run.detector_IBIL_QE65000


def test_form_doesnt_reset_detector_if_corresponding_method_selected():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_LE0": True,
        }
    )
    run = form.save(commit=False)
    assert run.detector_LE0


def test_form_resets_filters_if_corresponding_detector_unselected():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_HE2": False,
            "filters_for_detector_HE2": "something",
        }
    )
    run = form.save(commit=False)
    assert run.filters_for_detector_HE2 == ""


def test_form_resets_filters_if_corresponding_detector_not_posted():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "filters_for_detector_LE0": "Air",
        }
    )
    run = form.save(commit=False)
    assert not run.filters_for_detector_LE0


def test_form_resets_filters_if_corresponding_method_unselected():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": False,
            "detector_LE0": True,
            "filters_for_detector_LE0": "Air",
        }
    )
    run = form.save(commit=False)
    assert not run.filters_for_detector_LE0


def test_form_resets_filters_if_corresponding_method_not_posted():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "detector_LE0": True,
            "filters_for_detector_LE0": "Air",
        }
    )
    run = form.save(commit=False)
    assert not run.filters_for_detector_LE0


def test_form_doesnt_reset_filters_if_corresponding_detector_and_method_selected():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_LE0": True,
            "filters_for_detector_LE0": "Air",
        }
    )
    run = form.save(commit=False)
    assert run.filters_for_detector_LE0 == "Air"


def test_form_rejects_freeform_filter_if_not_in_config():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_LE0": True,
            "filters_for_detector_LE0": "Gotcha",
        }
    )
    assert form.has_error("filters_for_detector_LE0", code="invalid-filters-choice")


def test_form_validates_freeform_filter_if_in_config():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_HE1": True,
            "filters_for_detector_HE1": "Whatever",
        }
    )
    run = form.save(commit=False)
    assert run.filters_for_detector_HE1 == "Whatever"


def test_form_validates_empty_filter():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_LE0": True,
            "filters_for_detector_LE0": "",
            "detector_HE1": True,
            "filters_for_detector_HE1": "",
        }
    )
    assert form.is_valid()


def test_form_validates_missing_filter():
    form = RunDetailsForm(
        data={
            "label": "needed",
            "beamline": "Microbeam",
            "method_PIXE": True,
            "detector_LE0": True,
            "detector_HE1": True,
        }
    )
    assert form.is_valid()


# Beware!
def test_boolean_instance_data_is_not_kept_if_no_data_posted():
    form = RunDetailsForm(
        instance=factories.RunFactory.build(
            method_PIXE=True, detector_LE0=True, filters_for_detector_LE0="Air"
        ),
        data={"label": "needed", "beamline": "Microbeam"},
    )
    run = form.save(commit=False)
    assert not run.method_PIXE
    assert not run.detector_LE0
    assert (
        run.filters_for_detector_LE0 == "Air"
    )  # This one is kept. This is specific to some django logic


def test_form_assigns_choices_with_empty_default_to_regular_filters():
    form = RunDetailsForm()
    assert form["filters_for_detector_LE0"].widget_type == "select"
    assert form["filters_for_detector_LE0"].field.widget.choices == [
        ("", ""),
        ("Helium", "Helium"),
        ("Air", "Air"),
    ]


def test_form_assigns_choices_to_optional_freeform_filters():
    form = RunDetailsForm()
    assert form["filters_for_detector_HE1"].widget_type == "selectwithfreeother"


def test_freeform_filter_widget_contains_input_text_field():
    form = RunDetailsForm()
    assert '<input class="other-input" name="filters_for_detector_HE1" >' in str(
        form["filters_for_detector_HE1"]
    )
