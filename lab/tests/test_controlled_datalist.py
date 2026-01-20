import re
from unittest.mock import patch

import pytest
from django.db.models.query import QuerySet

from euphrosyne.methods.forms import AglaeRunDetailsForm as RunDetailsForm

from .factories import RunFactory

# [TODO] Test the front-end behavior with Cypress for example


@pytest.mark.django_db
def test_shows_datalists():
    form = RunDetailsForm()
    assert "<datalist" in str(form)
    assert str(form).count("</datalist>") == 3


@pytest.mark.django_db
def test_inputs_are_rendered_with_the_current_value():
    run = RunFactory()
    form = RunDetailsForm(instance=run)
    assert len(re.findall(f'<input[^>]*value="{run.energy_in_keV}"', str(form))) == 3


def test_form_cleans_the_multiple_inputs_into_one():
    form = RunDetailsForm(
        data={
            "label": "I am mandatory",
            "beamline": "Microbeam",
            "energy_in_keV_Proton": 1,
            "energy_in_keV_Alpha particle": 2,
            "energy_in_keV_Deuton": 3,
            "particle_type": "Deuton",
        }
    )
    with patch.object(QuerySet, "exists", return_value=False):
        assert form.is_valid()
    run = form.save(commit=False)
    assert run.energy_in_keV == 3


def test_form_allows_empty_value():
    form = RunDetailsForm(
        data={
            "label": "I am mandatory",
            "beamline": "Microbeam",
            "energy_in_keV_Proton": 1,
            "energy_in_keV_Alpha particle": 2,
            "energy_in_keV_Deuton": "",
            "particle_type": "Deuton",
        }
    )
    with patch.object(QuerySet, "exists", return_value=False):
        assert form.is_valid()
    run = form.save(commit=False)
    assert run.energy_in_keV is None


def test_form_stores_empty_controlled_value_if_controller_is_empty():
    form = RunDetailsForm(
        data={
            "label": "I am mandatory",
            "beamline": "Microbeam",
            "energy_in_keV_Proton": 1,
            "energy_in_keV_Alpha particle": 2,
            "energy_in_keV_Deuton": 3,
        }
    )
    with patch.object(QuerySet, "exists", return_value=False):
        assert form.is_valid()
    run = form.save(commit=False)
    assert run.energy_in_keV is None


def test_form_fails_gracefully_with_incoherent_controller_input():
    form = RunDetailsForm(
        data={
            "label": "I am mandatory",
            "beamline": "Microbeam",
            "energy_in_keV_Proton": 1,
            "energy_in_keV_Alpha particle": 2,
            "energy_in_keV_Deuton": "",
            "particle_type": "Gotcha",
        }
    )
    with patch.object(QuerySet, "exists", return_value=False):
        assert form.has_error("particle_type", code="invalid_choice")


def test_form_doesnt_raise_for_energy_when_other_errors():
    form = RunDetailsForm(
        data={
            "beamline": "WRONG",
            "energy_in_keV_Proton": 1,
            "energy_in_keV_Alpha particle": 2,
            "energy_in_keV_Deuton": "",
            "particle_type": "Gotcha",
            "start_date": "2021-01-01",
            "end_date": "2020-01-01",
        }
    )
    with patch.object(QuerySet, "exists", return_value=False):
        assert not form.is_valid()
    assert form.has_error("beamline")
    assert not form.has_error("energy_in_keV")
