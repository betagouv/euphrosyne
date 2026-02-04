from datetime import timedelta

import pytest
from django.utils import timezone

from data_management.models import ProjectData
from lab.runs.models import Run
from lab.runs.signals import run_scheduled
from lab.tests.factories import ProjectFactory, RunFactory


@pytest.mark.django_db
def test_project_data_created_with_initial_eligibility():
    project = ProjectFactory()

    project_data = ProjectData.objects.get(project=project)

    expected = project.created + timedelta(days=30 * 6)
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_run_scheduled_updates_project_eligibility():
    project = ProjectFactory()
    early_end_date = timezone.now() + timedelta(days=2)
    late_end_date = timezone.now() + timedelta(days=7)
    RunFactory(project=project, end_date=late_end_date)
    run = RunFactory(project=project, end_date=early_end_date)
    project_data = ProjectData.objects.get(project=project)

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    expected = late_end_date + timedelta(days=30 * 6)
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_run_scheduled_uses_latest_end_date_even_when_instance_missing_end_date():
    project = ProjectFactory()
    latest_end_date = timezone.now() + timedelta(days=10)
    RunFactory(project=project, end_date=latest_end_date)
    run = RunFactory(project=project, end_date=None)
    project_data = ProjectData.objects.get(project=project)

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    expected = latest_end_date + timedelta(days=30 * 6)
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_run_scheduled_keeps_eligibility_when_no_runs_have_end_date():
    run = RunFactory(end_date=None)
    project_data = ProjectData.objects.get(project=run.project)
    expected = project_data.cooling_eligible_at

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    assert project_data.cooling_eligible_at == expected
