from unittest.mock import patch

import pytest
from django.db.models import QuerySet
from django.utils import timezone

from .... import forms, models


@pytest.fixture(scope="module", autouse=True)
def patch_queryset_exists():
    with patch.object(QuerySet, "exists", return_value=False) as _fixture:
        yield _fixture


def test_run_dates_are_coherent():
    form = forms.RunScheduleForm(
        data={
            "start_date_0": "2021-01-01",
            "start_date_1": "00:00:00",
            "end_date_0": "2020-01-01",
            "end_date_1": "00:00:00",
        }
    )
    assert form.has_error("end_date", code="start_date_after_end_date")


def test_initial_embargo_in_two_years():
    form = forms.RunScheduleForm()
    assert form.initial["embargo_date"]
    assert form.initial["embargo_date"] > (
        timezone.now() + timezone.timedelta(days=(365 * 2) - 1)
    )


def test_no_initial_embargo_when_instance():
    now = timezone.now()
    run = models.Run(embargo_date=now)
    form = forms.RunScheduleForm(instance=run)
    assert not form.fields["embargo_date"].initial


def test_embargo_widget():
    form = forms.RunScheduleForm()
    assert form.fields["embargo_date"].widget.format == "%Y-%m-%d"
    assert form.fields["embargo_date"].widget.input_type == "date"
