from __future__ import annotations

import json
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.test.utils import override_settings
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)
from data_management.operations import is_retryable_operation
from data_management.reconciliation import (
    fail_stale_lifecycle_operations,
    get_stale_after,
)

from .factories import ProjectDataFactory


def _operation(project_data, *, operation_type, status, started_ago_hours):
    return LifecycleOperation.objects.create(
        project_data=project_data,
        type=operation_type,
        status=status,
        started_at=timezone.now() - timedelta(hours=started_ago_hours),
    )


@pytest.mark.django_db
def test_stale_cool_operation_fails_and_project_moves_to_error():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=7,
    )

    results = fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert [r.operation_id for r in results] == [str(operation.operation_id)]
    assert results[0].project_moved_to_error is True
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.finished_at is not None
    assert "no completion callback" in operation.error_message
    assert json.loads(operation.error_details)["reason"] == "stale_operation"
    assert project_data.lifecycle_state == LifecycleState.ERROR
    assert is_retryable_operation(project_data)


@pytest.mark.django_db
def test_stale_restore_operation_moves_project_to_error_and_stays_retryable():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.RESTORING)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=48,
    )

    fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert operation.status == LifecycleOperationStatus.FAILED
    assert project_data.lifecycle_state == LifecycleState.ERROR
    assert is_retryable_operation(project_data)


@pytest.mark.django_db
def test_recent_operation_is_left_alone():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=1,
    )

    results = fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert not results
    assert operation.status == LifecycleOperationStatus.RUNNING
    assert project_data.lifecycle_state == LifecycleState.COOLING


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [LifecycleOperationStatus.SUCCEEDED, LifecycleOperationStatus.FAILED],
)
def test_old_finished_operation_is_left_alone(status):
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOL)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=status,
        started_ago_hours=100,
    )

    results = fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert not results
    assert operation.status == status
    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
def test_stale_pending_operation_on_hot_project_does_not_change_project():
    # The request to the tools API never went out: the project is still HOT.
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.PENDING,
        started_ago_hours=10,
    )

    results = fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert results[0].project_moved_to_error is False
    assert operation.status == LifecycleOperationStatus.FAILED
    assert project_data.lifecycle_state == LifecycleState.HOT


@pytest.mark.django_db
def test_project_state_not_matching_operation_type_is_not_touched():
    # Stale RESTORE operation but the project is COOLING (a newer cool is running).
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=10,
    )

    fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert operation.status == LifecycleOperationStatus.FAILED
    assert project_data.lifecycle_state == LifecycleState.COOLING


@pytest.mark.django_db
def test_dry_run_reports_without_writing():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=7,
    )

    results = fail_stale_lifecycle_operations(
        stale_after=timedelta(hours=6), dry_run=True
    )

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert len(results) == 1
    assert operation.status == LifecycleOperationStatus.RUNNING
    assert operation.finished_at is None
    assert project_data.lifecycle_state == LifecycleState.COOLING


@pytest.mark.django_db
def test_second_run_is_a_noop():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=7,
    )

    first = fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))
    second = fail_stale_lifecycle_operations(stale_after=timedelta(hours=6))

    assert len(first) == 1
    assert not second


@pytest.mark.django_db
def test_get_stale_after_reads_setting():
    with override_settings(DATA_LIFECYCLE_OPERATION_TIMEOUT_HOURS=2):
        assert get_stale_after() == timedelta(hours=2)
    assert get_stale_after() == timedelta(hours=6)


@pytest.mark.django_db
def test_command_fails_stale_operations_and_reports():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=7,
    )
    out = StringIO()

    call_command("reconcile_lifecycle_operations", stdout=out)

    operation.refresh_from_db()
    project_data.refresh_from_db()
    assert operation.status == LifecycleOperationStatus.FAILED
    assert project_data.lifecycle_state == LifecycleState.ERROR
    assert project_data.project.slug in out.getvalue()
    assert "Failed 1 stale lifecycle operation(s)." in out.getvalue()


@pytest.mark.django_db
def test_command_dry_run_and_custom_threshold():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = _operation(
        project_data,
        operation_type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_ago_hours=2,
    )
    out = StringIO()

    call_command(
        "reconcile_lifecycle_operations",
        "--dry-run",
        "--stale-after-hours=1",
        stdout=out,
    )

    operation.refresh_from_db()
    assert operation.status == LifecycleOperationStatus.RUNNING
    assert "[dry-run]" in out.getvalue()
    assert "Found 1 stale lifecycle operation(s)." in out.getvalue()
