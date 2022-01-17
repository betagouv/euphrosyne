from unittest.mock import patch

import pytest
from django.db.models import QuerySet

from .... import forms


@pytest.fixture(scope="module", autouse=True)
def patch_queryset_exists():
    with patch.object(QuerySet, "exists", return_value=False) as _fixture:
        yield _fixture


def test_beamline_is_validated():
    form = forms.RunDetailsForm(data={"label": "needed", "beamline": "phony"})
    assert form.has_error("beamline")


def test_run_dates_are_coherent():
    form = forms.RunDetailsForm(
        data={"start_date": "2021-01-01", "end_date": "2020-01-01"}
    )
    assert form.has_error("end_date", code="start_date_after_end_date")
