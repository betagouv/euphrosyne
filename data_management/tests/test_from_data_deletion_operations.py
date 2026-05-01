from __future__ import annotations

from unittest import mock

import pytest
import requests
from django.utils import timezone

from data_management.models import (
    FromDataDeletionStatus,
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)
from data_management.operations import (
    FromDataDeletionNotAllowedError,
    FromDataDeletionStartError,
    resolve_from_storage_role,
    trigger_from_data_deletion,
)

from .factories import ProjectDataFactory


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


# pylint: disable=too-many-arguments
def create_operation(
    *,
    lifecycle_state: str = LifecycleState.COOL,
    operation_type: str = LifecycleOperationType.COOL,
    status: str = LifecycleOperationStatus.SUCCEEDED,
    bytes_total: int | None = 10,
    files_total: int | None = 2,
    from_data_deletion_status: str = FromDataDeletionStatus.NOT_REQUESTED,
    from_data_deleted_at=None,
    from_data_deletion_error: str | None = None,
) -> LifecycleOperation:
    project_data = ProjectDataFactory(lifecycle_state=lifecycle_state)
    return LifecycleOperation.objects.create(
        project_data=project_data,
        type=operation_type,
        status=status,
        started_at=timezone.now(),
        finished_at=timezone.now(),
        bytes_total=bytes_total,
        files_total=files_total,
        bytes_copied=bytes_total,
        files_copied=files_total,
        from_data_deletion_status=from_data_deletion_status,
        from_data_deleted_at=from_data_deleted_at,
        from_data_deletion_error=from_data_deletion_error,
    )


def test_resolve_from_storage_role_maps_lifecycle_operation_type():
    assert resolve_from_storage_role(LifecycleOperationType.COOL) == LifecycleState.HOT
    assert resolve_from_storage_role(LifecycleOperationType.RESTORE) == (
        LifecycleState.COOL
    )


@pytest.mark.django_db
def test_trigger_from_data_deletion_for_eligible_cool_operation_calls_tools_api():
    operation = create_operation(bytes_total=1234567890, files_total=122)

    with mock.patch(
        "data_management.operations.post_delete_project_source_data",
        return_value=DummyResponse(status_code=202),
    ) as delete_mock:
        result = trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()

    assert result.operation_id == operation.operation_id
    assert operation.from_data_deletion_status == FromDataDeletionStatus.RUNNING
    assert operation.from_data_deleted_at is None
    assert operation.from_data_deletion_error is None
    delete_mock.assert_called_once_with(
        project_slug=operation.project_data.project.slug,
        storage_role=LifecycleState.HOT,
        operation_id=str(operation.operation_id),
        file_count=122,
        total_size=1234567890,
        timeout=10,
    )


@pytest.mark.django_db
def test_trigger_from_data_deletion_for_eligible_restore_operation_calls_tools_api():
    operation = create_operation(
        operation_type=LifecycleOperationType.RESTORE,
        lifecycle_state=LifecycleState.HOT,
        bytes_total=9876543210,
        files_total=321,
    )

    with mock.patch(
        "data_management.operations.post_delete_project_source_data",
        return_value=DummyResponse(status_code=202),
    ) as delete_mock:
        result = trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()

    assert result.operation_id == operation.operation_id
    assert operation.from_data_deletion_status == FromDataDeletionStatus.RUNNING
    assert operation.from_data_deleted_at is None
    assert operation.from_data_deletion_error is None
    delete_mock.assert_called_once_with(
        project_slug=operation.project_data.project.slug,
        storage_role=LifecycleState.COOL,
        operation_id=str(operation.operation_id),
        file_count=321,
        total_size=9876543210,
        timeout=10,
    )

    kwargs = delete_mock.call_args.kwargs
    assert isinstance(kwargs["file_count"], int)
    assert isinstance(kwargs["total_size"], int)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "missing_totals",
    [
        {"files_total": None, "bytes_total": 10},
        {"files_total": 2, "bytes_total": None},
    ],
)
def test_trigger_from_data_deletion_rejects_missing_active_storage_totals(
    missing_totals,
):
    operation = create_operation(**missing_totals)

    with mock.patch(
        "data_management.operations.post_delete_project_source_data"
    ) as post_mock:
        with pytest.raises(FromDataDeletionNotAllowedError):
            trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()

    assert operation.from_data_deletion_status == FromDataDeletionStatus.NOT_REQUESTED
    post_mock.assert_not_called()


@pytest.mark.django_db
def test_trigger_from_data_deletion_retry_from_failed_resets_running_state():
    operation = create_operation(
        from_data_deletion_status=FromDataDeletionStatus.FAILED,
        from_data_deleted_at=timezone.now(),
        from_data_deletion_error="previous error",
    )

    with mock.patch(
        "data_management.operations.post_delete_project_source_data",
        return_value=DummyResponse(status_code=202),
    ):
        trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()

    assert operation.from_data_deletion_status == FromDataDeletionStatus.RUNNING
    assert operation.from_data_deleted_at is None
    assert operation.from_data_deletion_error is None


@pytest.mark.django_db
def test_trigger_from_data_deletion_marks_failed_when_tools_api_is_unavailable():
    operation = create_operation()

    with mock.patch(
        "data_management.operations.post_delete_project_source_data",
        side_effect=requests.RequestException("boom"),
    ):
        with pytest.raises(FromDataDeletionStartError):
            trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert operation.from_data_deletion_status == FromDataDeletionStatus.FAILED
    assert operation.from_data_deletion_error == "boom"
    assert operation.status == LifecycleOperationStatus.SUCCEEDED
    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
def test_trigger_from_data_deletion_marks_failed_when_tools_api_rejects_request():
    operation = create_operation()

    with mock.patch(
        "data_management.operations.post_delete_project_source_data",
        return_value=DummyResponse(status_code=500, text="server error"),
    ):
        with pytest.raises(FromDataDeletionStartError):
            trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert operation.from_data_deletion_status == FromDataDeletionStatus.FAILED
    assert operation.from_data_deletion_error == "server error"
    assert operation.status == LifecycleOperationStatus.SUCCEEDED
    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("status", "deletion_status"),
    [
        (
            LifecycleOperationStatus.FAILED,
            FromDataDeletionStatus.NOT_REQUESTED,
        ),
        (
            LifecycleOperationStatus.SUCCEEDED,
            FromDataDeletionStatus.SUCCEEDED,
        ),
    ],
)
def test_trigger_from_data_deletion_rejects_ineligible_operations(
    status: str,
    deletion_status: str,
):
    operation = create_operation(
        status=status,
        from_data_deletion_status=deletion_status,
    )

    with mock.patch(
        "data_management.operations.post_delete_project_source_data"
    ) as post_mock:
        with pytest.raises(FromDataDeletionNotAllowedError):
            trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()

    assert operation.from_data_deletion_status == deletion_status
    post_mock.assert_not_called()


@pytest.mark.django_db
def test_trigger_from_data_deletion_rejects_when_another_active_operation_exists():
    operation = create_operation()
    LifecycleOperation.objects.create(
        project_data=operation.project_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.RUNNING,
        started_at=timezone.now(),
    )

    with mock.patch(
        "data_management.operations.post_delete_project_source_data"
    ) as post_mock:
        with pytest.raises(FromDataDeletionNotAllowedError):
            trigger_from_data_deletion(operation.operation_id)

    operation.refresh_from_db()

    assert operation.from_data_deletion_status == FromDataDeletionStatus.NOT_REQUESTED
    post_mock.assert_not_called()
