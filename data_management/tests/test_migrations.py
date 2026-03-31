from datetime import timedelta
from importlib import import_module

import pytest
from django.utils import timezone

from lab.runs.models import Run
from lab.tests.factories import ProjectFactory, RunFactory

migration = import_module("data_management.migrations.0004_backfill_project_data")


@pytest.mark.django_db
def test_backfill_cooling_eligible_at_uses_latest_runtime_candidate():
    project = ProjectFactory()
    earlier_embargo_date = timezone.localdate() + timedelta(days=10)
    later_end_date = timezone.now() + timedelta(days=20)

    RunFactory(project=project, end_date=None, embargo_date=earlier_embargo_date)
    RunFactory(project=project, end_date=later_end_date, embargo_date=None)

    expected = timezone.localdate(later_end_date + timedelta(days=30 * 24))

    # pylint: disable=protected-access
    assert migration._compute_cooling_eligible_at(project, Run) == expected


@pytest.mark.django_db
def test_backfill_cooling_eligible_at_ignores_end_date_when_run_has_embargo():
    project = ProjectFactory()
    embargo_date = timezone.localdate() + timedelta(days=10)
    later_end_date = timezone.now() + timedelta(days=20)

    RunFactory(project=project, end_date=later_end_date, embargo_date=embargo_date)

    # pylint: disable=protected-access
    assert migration._compute_cooling_eligible_at(project, Run) == embargo_date
