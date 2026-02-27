from unittest.mock import patch

import pytest
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.models import QuerySet
from django.test import override_settings
from django.utils import timezone

from ....tests import factories
from ... import forms, models


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


def test_set_permanent_embargo_when_embargo_not_in_data():
    run = models.Run(embargo_date=None)
    form = forms.RunScheduleForm(
        data={
            "start_date_0": "2021-01-01",
            "start_date_1": "00:00:00",
            "end_date_0": "2021-01-01",
            "end_date_1": "00:00:00",
        },
        instance=run,
    )
    assert form.fields["permanent_embargo"].initial is True


def test_absent_permanent_embargo_when_embargo_in_data():
    form = forms.RunScheduleForm(
        data={
            "start_date_0": "2021-01-01",
            "start_date_1": "00:00:00",
            "end_date_0": "2021-01-01",
            "end_date_1": "00:00:00",
            "embargo_date": "2021-01-01",
        }
    )
    assert not form.fields["permanent_embargo"].initial


def test_set_embargo_date_when_embargo_not_in_data():
    run = models.Run(embargo_date=timezone.now().date())
    form = forms.RunScheduleForm(
        data={
            "start_date_0": "2021-01-01",
            "start_date_1": "00:00:00",
            "end_date_0": "2021-01-01",
            "end_date_1": "00:00:00",
        },
        instance=run,
    )
    assert form.instance.embargo_date is None


def test_embargo_widget():
    form = forms.RunScheduleForm()
    assert form.fields["embargo_date"].widget.format == "%Y-%m-%d"
    assert form.fields["embargo_date"].widget.input_type == "date"


def _get_schedule_data():
    return {
        "start_date_0": "2021-01-01",
        "start_date_1": "00:00:00",
        "end_date_0": "2021-01-02",
        "end_date_1": "00:00:00",
        "embargo_date": "2021-01-10",
    }


@pytest.mark.django_db
def test_first_schedule_requires_employer_for_on_premises_participations():
    run = factories.RunFactory(start_date=None, end_date=None)
    factories.ParticipationFactory(
        project=run.project,
        on_premises=True,
        employer=None,
    )

    form = forms.RunScheduleForm(data=_get_schedule_data(), instance=run)

    assert form.has_error(NON_FIELD_ERRORS, code="missing_participation_employer")


@pytest.mark.django_db
def test_reschedule_does_not_require_employer_for_on_premises_participations():
    run = factories.RunFactory()
    factories.ParticipationFactory(
        project=run.project,
        on_premises=True,
        employer=None,
    )

    form = forms.RunScheduleForm(data=_get_schedule_data(), instance=run)

    assert form.is_valid()


@pytest.mark.django_db
def test_first_schedule_allows_missing_employer_for_remote_participations():
    run = factories.RunFactory(start_date=None, end_date=None)
    factories.ParticipationFactory(
        project=run.project,
        on_premises=False,
        employer=None,
    )

    form = forms.RunScheduleForm(data=_get_schedule_data(), instance=run)

    assert form.is_valid()


@pytest.mark.django_db
@override_settings(
    PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS=["https://ror.org/exempt"]
)
def test_first_schedule_allows_missing_employer_for_exempt_institution():
    run = factories.RunFactory(start_date=None, end_date=None)
    institution = factories.InstitutionFactory(ror_id="https://ror.org/exempt")
    factories.ParticipationFactory(
        project=run.project,
        institution=institution,
        on_premises=True,
        employer=None,
    )

    form = forms.RunScheduleForm(data=_get_schedule_data(), instance=run)

    assert form.is_valid()
