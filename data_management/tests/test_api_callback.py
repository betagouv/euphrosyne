from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client
from django.utils import timezone

from data_management.models import (
    FromDataDeletionStatus,
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)
from euphro_auth.jwt.tokens import EuphroToolsAPIToken

from .factories import ProjectDataFactory

CALLBACK_URL = "/api/data-management/operations/callback"


def _backend_headers() -> dict[str, str]:
    token = EuphroToolsAPIToken.for_euphrosyne()
    return {"Authorization": f"Bearer {token}"}


def _create_operation(  # pylint: disable=too-many-arguments
    *,
    lifecycle_state: str,
    operation_type: str = LifecycleOperationType.COOL,
    status: str = LifecycleOperationStatus.RUNNING,
    bytes_total: int = 10,
    files_total: int = 2,
    bytes_copied: int | None = None,
    files_copied: int | None = None,
    error_message: str | None = None,
) -> LifecycleOperation:
    project_data = ProjectDataFactory(
        lifecycle_state=lifecycle_state,
    )
    return LifecycleOperation.objects.create(
        project_data=project_data,
        type=operation_type,
        status=status,
        started_at=timezone.now(),
        bytes_total=bytes_total,
        files_total=files_total,
        bytes_copied=bytes_copied,
        files_copied=files_copied,
        error_message=error_message,
    )


@pytest.mark.django_db
def test_callback_requires_backend_authentication():
    operation = _create_operation(lifecycle_state=LifecycleState.COOLING)

    response = Client().post(
        CALLBACK_URL,
        data={"operation_id": str(operation.operation_id), "status": "FAILED"},
        content_type="application/json",
    )

    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_callback_returns_not_found_for_unknown_operation_id():
    response = Client().post(
        CALLBACK_URL,
        data={"operation_id": str(uuid.uuid4()), "status": "FAILED"},
        headers=_backend_headers(),
        content_type="application/json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_callback_failed_marks_operation_failed_and_project_error():
    operation = _create_operation(lifecycle_state=LifecycleState.COOLING)

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "status": "FAILED",
            "error_message": "AzCopy job failed.",
            "error_details": {"code": "AZCOPY_FAILURE", "message": "job failed"},
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "AzCopy job failed."
    assert json.loads(operation.error_details or "{}") == {
        "code": "AZCOPY_FAILURE",
        "message": "job failed",
    }
    assert project_data.lifecycle_state == LifecycleState.ERROR


@pytest.mark.django_db
def test_callback_succeeded_verified_transitions_cool_operation_to_cool():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOLING,
        operation_type=LifecycleOperationType.COOL,
    )

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "status": "SUCCEEDED",
            "bytes_total": 10,
            "files_total": 2,
            "bytes_copied": 10,
            "files_copied": 2,
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.SUCCEEDED
    assert operation.bytes_copied == 10
    assert operation.files_copied == 2
    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
def test_callback_succeeded_verified_transitions_restore_operation_to_hot():
    operation = _create_operation(
        lifecycle_state=LifecycleState.RESTORING,
        operation_type=LifecycleOperationType.RESTORE,
    )

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "status": "SUCCEEDED",
            "bytes_total": 10,
            "files_total": 2,
            "bytes_copied": 10,
            "files_copied": 2,
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.SUCCEEDED
    assert project_data.lifecycle_state == LifecycleState.HOT


@pytest.mark.django_db
def test_callback_succeeded_with_mismatch_marks_failed_and_project_error():
    operation = _create_operation(lifecycle_state=LifecycleState.COOLING)

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "status": "SUCCEEDED",
            "bytes_total": 10,
            "files_total": 2,
            "bytes_copied": 9,
            "files_copied": 2,
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "Verification failed."
    assert json.loads(operation.error_details or "{}") == {
        "expected": {"bytes_total": 10, "files_total": 2},
        "reason": "verification_mismatch",
        "received": {"bytes_copied": 9, "files_copied": 2},
    }
    assert project_data.lifecycle_state == LifecycleState.ERROR


@pytest.mark.django_db
def test_callback_succeeded_without_totals_marks_failed_and_project_error():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOLING,
        bytes_total=1000,
        files_total=200,
    )

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "status": "SUCCEEDED",
            "bytes_copied": None,
            "files_copied": None,
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "Verification failed."
    assert operation.bytes_total == 1000
    assert operation.files_total == 200
    assert json.loads(operation.error_details or "{}") == {
        "expected": {"bytes_total": 1000, "files_total": 200},
        "reason": "verification_mismatch",
        "received": {"bytes_copied": None, "files_copied": None},
    }
    assert project_data.lifecycle_state == LifecycleState.ERROR


@pytest.mark.django_db
def test_callback_is_idempotent_when_operation_is_already_terminal():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
        bytes_copied=10,
        files_copied=2,
        error_message="original message",
    )
    initial_finished_at = operation.finished_at

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "status": "FAILED",
            "error_message": "ignored duplicate callback",
            "error_details": {"ignored": True},
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.SUCCEEDED
    assert operation.error_message == "original message"
    assert operation.finished_at == initial_finished_at
    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
def test_callback_failed_does_not_bypass_invalid_transition_to_error():
    operation = _create_operation(lifecycle_state=LifecycleState.HOT)

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "status": "FAILED",
            "error_message": "Tools failure.",
            "error_details": {"reason": "unexpected"},
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "Tools failure."
    assert project_data.lifecycle_state == LifecycleState.HOT


@pytest.mark.django_db
def test_callback_from_data_deletion_succeeded_updates_only_deletion_fields():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
        error_message="keep me",
    )
    operation.from_data_deletion_status = FromDataDeletionStatus.RUNNING
    operation.save(update_fields=["from_data_deletion_status"])

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "phase": "FROM_DATA_DELETION",
            "from_data_deletion_status": "SUCCEEDED",
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.SUCCEEDED
    assert operation.error_message == "keep me"
    assert operation.from_data_deletion_status == FromDataDeletionStatus.SUCCEEDED
    assert operation.from_data_deleted_at is not None
    assert operation.from_data_deletion_error is None
    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
def test_callback_from_data_deletion_failed_persists_error_without_state_change():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
    )
    operation.from_data_deletion_status = FromDataDeletionStatus.RUNNING
    operation.save(update_fields=["from_data_deletion_status"])

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "phase": "FROM_DATA_DELETION",
            "from_data_deletion_status": "FAILED",
            "error": {"code": "DELETE_FAILED", "message": "failed"},
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()
    project_data = operation.project_data
    project_data.refresh_from_db()

    assert response.status_code == 200
    assert operation.status == LifecycleOperationStatus.SUCCEEDED
    assert operation.from_data_deletion_status == FromDataDeletionStatus.FAILED
    assert operation.from_data_deleted_at is None
    assert json.loads(operation.from_data_deletion_error or "{}") == {
        "code": "DELETE_FAILED",
        "message": "failed",
    }
    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
def test_callback_from_data_deletion_failed_uses_default_error_when_missing():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
    )
    operation.from_data_deletion_status = FromDataDeletionStatus.RUNNING
    operation.save(update_fields=["from_data_deletion_status"])

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "phase": "FROM_DATA_DELETION",
            "from_data_deletion_status": "FAILED",
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()

    assert response.status_code == 200
    assert operation.from_data_deletion_status == FromDataDeletionStatus.FAILED
    assert (
        operation.from_data_deletion_error
        == "Tools API reported source data deletion failure."
    )


@pytest.mark.django_db
def test_callback_from_data_deletion_is_idempotent_when_already_terminal():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
    )
    deleted_at = timezone.now()
    operation.from_data_deletion_status = FromDataDeletionStatus.SUCCEEDED
    operation.from_data_deleted_at = deleted_at
    operation.save(update_fields=["from_data_deletion_status", "from_data_deleted_at"])

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "phase": "FROM_DATA_DELETION",
            "from_data_deletion_status": "FAILED",
            "error": "ignored duplicate callback",
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()

    assert response.status_code == 200
    assert operation.from_data_deletion_status == FromDataDeletionStatus.SUCCEEDED
    assert operation.from_data_deleted_at == deleted_at
    assert operation.from_data_deletion_error is None


@pytest.mark.django_db
def test_callback_from_data_deletion_is_ignored_when_not_requested():
    operation = _create_operation(
        lifecycle_state=LifecycleState.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
    )

    response = Client().post(
        CALLBACK_URL,
        data={
            "operation_id": str(operation.operation_id),
            "phase": "FROM_DATA_DELETION",
            "from_data_deletion_status": "SUCCEEDED",
        },
        headers=_backend_headers(),
        content_type="application/json",
    )

    operation.refresh_from_db()

    assert response.status_code == 200
    assert operation.from_data_deletion_status == FromDataDeletionStatus.NOT_REQUESTED
    assert operation.from_data_deleted_at is None
    assert operation.from_data_deletion_error is None
