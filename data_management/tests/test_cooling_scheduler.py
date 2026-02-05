from __future__ import annotations

from datetime import timedelta
from unittest import mock

import pytest
import requests
from django.test.utils import override_settings
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)
from data_management.scheduler import run_cooling_scheduler

from .factories import ProjectDataFactory


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


@pytest.mark.django_db
@override_settings(DATA_COOLING_ENABLE=False)
def test_scheduler_disabled_does_nothing():
    project_data = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timedelta(days=1),
        project_size_bytes=10,
        file_count=2,
    )

    enqueued = run_cooling_scheduler()

    project_data.refresh_from_db()

    assert enqueued == 0
    assert project_data.lifecycle_state == LifecycleState.HOT
    assert LifecycleOperation.objects.count() == 0


@pytest.mark.django_db
@override_settings(DATA_COOLING_ENABLE=True)
def test_scheduler_enqueues_oldest_three(monkeypatch):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "http://tools.example.com")

    now = timezone.now()
    project_data_oldest = ProjectDataFactory(
        cooling_eligible_at=now - timedelta(days=4),
        project_size_bytes=100,
        file_count=5,
    )
    project_data_second = ProjectDataFactory(
        cooling_eligible_at=now - timedelta(days=3),
        project_size_bytes=200,
        file_count=6,
    )
    project_data_third = ProjectDataFactory(
        cooling_eligible_at=now - timedelta(days=2),
        project_size_bytes=300,
        file_count=7,
    )
    project_data_newest = ProjectDataFactory(
        cooling_eligible_at=now - timedelta(days=1),
        project_size_bytes=400,
        file_count=8,
    )

    with mock.patch(
        "data_management.scheduler.post_cool_project",
        return_value=DummyResponse(status_code=202),
    ):
        enqueued = run_cooling_scheduler(limit=3)

    project_data_oldest.refresh_from_db()
    project_data_second.refresh_from_db()
    project_data_third.refresh_from_db()
    project_data_newest.refresh_from_db()

    assert enqueued == 3
    assert project_data_oldest.lifecycle_state == LifecycleState.COOLING
    assert project_data_second.lifecycle_state == LifecycleState.COOLING
    assert project_data_third.lifecycle_state == LifecycleState.COOLING
    assert project_data_newest.lifecycle_state == LifecycleState.HOT

    operations = list(
        LifecycleOperation.objects.filter(type=LifecycleOperationType.COOL)
    )
    assert len(operations) == 3
    assert all(op.status == LifecycleOperationStatus.RUNNING for op in operations)


@pytest.mark.django_db
@override_settings(DATA_COOLING_ENABLE=True)
def test_scheduler_marks_failed_when_tools_api_rejects():

    project_data = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timedelta(days=1),
        project_size_bytes=10,
        file_count=2,
    )

    with mock.patch(
        "data_management.scheduler.post_cool_project",
        return_value=DummyResponse(status_code=400, text="Bad Request"),
    ):
        enqueued = run_cooling_scheduler()

    project_data.refresh_from_db()
    operation = LifecycleOperation.objects.get()

    assert enqueued == 0
    assert project_data.lifecycle_state == LifecycleState.HOT
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message


@pytest.mark.django_db
@override_settings(DATA_COOLING_ENABLE=True)
def test_scheduler_marks_failed_when_tools_api_raises_request_exception():
    project_data = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timedelta(days=1),
        project_size_bytes=10,
        file_count=2,
    )

    with mock.patch(
        "data_management.scheduler.post_cool_project",
        side_effect=requests.RequestException("boom"),
    ):
        enqueued = run_cooling_scheduler()

    project_data.refresh_from_db()
    operation = LifecycleOperation.objects.get()

    assert enqueued == 0
    assert project_data.lifecycle_state == LifecycleState.HOT
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message


@pytest.mark.django_db
@override_settings(DATA_COOLING_ENABLE=True)
def test_scheduler_skips_projects_with_active_pending_cool_operation():
    project_data_claimed = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timedelta(days=2),
        project_size_bytes=10,
        file_count=2,
    )
    LifecycleOperation.objects.create(
        project_data=project_data_claimed,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.PENDING,
    )

    project_data_fresh = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timedelta(days=1),
        project_size_bytes=10,
        file_count=2,
    )

    with mock.patch(
        "data_management.scheduler.post_cool_project",
        return_value=DummyResponse(status_code=202),
    ):
        enqueued = run_cooling_scheduler(limit=3)

    project_data_claimed.refresh_from_db()
    project_data_fresh.refresh_from_db()

    assert enqueued == 1
    assert project_data_claimed.lifecycle_state == LifecycleState.HOT
    assert project_data_fresh.lifecycle_state == LifecycleState.COOLING


@pytest.mark.django_db
@override_settings(DATA_COOLING_ENABLE=True)
def test_scheduler_skips_projects_with_active_running_cool_operation():
    project_data_claimed = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timedelta(days=2),
        project_size_bytes=10,
        file_count=2,
    )
    LifecycleOperation.objects.create(
        project_data=project_data_claimed,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
    )

    project_data_fresh = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timedelta(days=1),
        project_size_bytes=10,
        file_count=2,
    )

    with mock.patch(
        "data_management.scheduler.post_cool_project",
        return_value=DummyResponse(status_code=202),
    ):
        enqueued = run_cooling_scheduler(limit=3)

    project_data_claimed.refresh_from_db()
    project_data_fresh.refresh_from_db()

    assert enqueued == 1
    assert project_data_claimed.lifecycle_state == LifecycleState.HOT
    assert project_data_fresh.lifecycle_state == LifecycleState.COOLING
