from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest
from django.utils import timezone

from data_management.eligibility import compute_cooling_eligible_at
from data_management.models import ProjectData
from lab.runs.models import Run
from lab.runs.signals import run_scheduled
from lab.tests.factories import ProjectFactory, RunFactory


@pytest.mark.django_db
def test_project_data_created_with_initial_eligibility():
    project = ProjectFactory()

    project_data = ProjectData.objects.get(project=project)

    expected = timezone.localdate(project.created + timedelta(days=30 * 24))
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_setting_embargo_date_sets_project_eligibility():
    run = RunFactory(end_date=None, embargo_date=None)
    project_data = ProjectData.objects.get(project=run.project)
    embargo_date = timezone.localdate() + timedelta(days=10)

    run.embargo_date = embargo_date
    run.save(update_fields=["embargo_date"])

    project_data.refresh_from_db()
    assert project_data.cooling_eligible_at == embargo_date


@pytest.mark.django_db
def test_updating_embargo_date_recomputes_project_eligibility():
    project = ProjectFactory()
    initial_embargo_date = timezone.localdate() + timedelta(days=10)
    updated_embargo_date = initial_embargo_date + timedelta(days=7)
    run = RunFactory(
        project=project,
        end_date=None,
        embargo_date=initial_embargo_date,
    )
    project_data = ProjectData.objects.get(project=run.project)

    run.embargo_date = updated_embargo_date
    run.save(update_fields=["embargo_date"])

    project_data.refresh_from_db()
    assert project_data.cooling_eligible_at == updated_embargo_date


@pytest.mark.django_db
def test_run_scheduled_updates_project_eligibility_without_embargo():
    project = ProjectFactory()
    early_end_date = timezone.now() + timedelta(days=2)
    late_end_date = timezone.now() + timedelta(days=7)
    RunFactory(project=project, end_date=late_end_date, embargo_date=None)
    run = RunFactory(project=project, end_date=early_end_date, embargo_date=None)
    project_data = ProjectData.objects.get(project=project)

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    expected = timezone.localdate(late_end_date + timedelta(days=30 * 24))
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_run_scheduled_uses_later_non_embargo_candidate_over_embargo_date():
    project = ProjectFactory()
    embargo_date = timezone.localdate() + timedelta(days=10)
    late_end_date = timezone.now() + timedelta(days=20)
    RunFactory(project=project, end_date=None, embargo_date=embargo_date)
    run = RunFactory(
        project=project,
        end_date=late_end_date,
        embargo_date=None,
    )
    project_data = ProjectData.objects.get(project=project)
    expected = timezone.localdate(late_end_date + timedelta(days=30 * 24))

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_run_scheduled_uses_latest_end_date_even_when_instance_missing_end_date():
    project = ProjectFactory()
    latest_end_date = timezone.now() + timedelta(days=10)
    RunFactory(project=project, end_date=latest_end_date, embargo_date=None)
    run = RunFactory(project=project, end_date=None, embargo_date=None)
    project_data = ProjectData.objects.get(project=project)

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    expected = timezone.localdate(latest_end_date + timedelta(days=30 * 24))
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_run_scheduled_keeps_later_embargo_candidate_over_non_embargo_date():
    project = ProjectFactory()
    embargo_date = timezone.localdate() + timedelta(days=40)
    end_date = timezone.now() - timedelta(days=700)
    RunFactory(project=project, end_date=end_date, embargo_date=None)
    run = RunFactory(project=project, end_date=None, embargo_date=embargo_date)
    project_data = ProjectData.objects.get(project=project)

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    assert project_data.cooling_eligible_at == embargo_date


@pytest.mark.django_db
def test_run_save_recomputes_stale_embargo_based_project_eligibility():
    project = ProjectFactory()
    embargo_date = timezone.localdate() + timedelta(days=10)
    later_end_date = timezone.now() + timedelta(days=20)
    run = RunFactory(project=project, end_date=None, embargo_date=embargo_date)
    RunFactory(project=project, end_date=later_end_date, embargo_date=None)
    project_data = ProjectData.objects.get(project=project)
    project_data.cooling_eligible_at = embargo_date
    project_data.save(update_fields=["cooling_eligible_at"])
    run.refresh_from_db()

    run.label = f"{run.label}-updated"
    run.save(update_fields=["label"])

    project_data.refresh_from_db()
    expected = timezone.localdate(later_end_date + timedelta(days=30 * 24))
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_run_scheduled_uses_local_date_for_latest_end_date():
    end_date = datetime(2026, 3, 12, 23, 30, tzinfo=dt_timezone.utc)
    run = RunFactory(end_date=end_date, embargo_date=None)
    project_data = ProjectData.objects.get(project=run.project)

    run_scheduled.send(sender=Run, instance=run)

    project_data.refresh_from_db()
    expected = timezone.localdate(end_date + timedelta(days=30 * 24))
    assert project_data.cooling_eligible_at == expected


@pytest.mark.django_db
def test_compute_cooling_eligible_at_uses_local_date_for_project_created_at():
    project = ProjectFactory()
    created_at = datetime(2026, 3, 12, 23, 30, tzinfo=dt_timezone.utc)
    project.__class__.objects.filter(pk=project.pk).update(created=created_at)
    project.refresh_from_db()

    expected = timezone.localdate(created_at + timedelta(days=30 * 24))
    assert compute_cooling_eligible_at(project) == expected
