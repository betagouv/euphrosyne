from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
)
from euphro_auth.tests import factories as auth_factories

from .factories import ProjectDataFactory


def _operation_url(operation_id: uuid.UUID) -> str:
    return f"/api/data-management/operations/{operation_id}"


@pytest.mark.django_db
def test_operation_detail_requires_lab_admin():
    operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(),
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.PENDING,
    )

    anon_response = Client().get(_operation_url(operation.operation_id))
    assert anon_response.status_code in {401, 403}

    staff_client = Client()
    staff_client.force_login(auth_factories.StaffUserFactory())
    staff_response = staff_client.get(_operation_url(operation.operation_id))
    assert staff_response.status_code == 403


@pytest.mark.django_db
def test_operation_detail_returns_not_found_for_unknown_operation():
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.get(_operation_url(uuid.uuid4()))

    assert response.status_code == 404


@pytest.mark.django_db
def test_operation_detail_returns_payload_with_bytes_based_progress():
    started_at = timezone.now()
    finished_at = timezone.now()
    project_data = ProjectDataFactory()
    operation = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_at=started_at,
        finished_at=finished_at,
        bytes_total=200,
        files_total=10,
        bytes_copied=50,
        files_copied=3,
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.get(_operation_url(operation.operation_id))
    payload = response.json()

    assert response.status_code == 200
    assert payload["operation_id"] == str(operation.operation_id)
    assert payload["project_id"] == project_data.project_id
    assert payload["type"] == LifecycleOperationType.COOL
    assert payload["status"] == LifecycleOperationStatus.RUNNING
    assert "created_at" not in payload
    assert payload["started_at"] is not None
    assert payload["finished_at"] is not None
    assert payload["bytes_total"] == 200
    assert payload["files_total"] == 10
    assert payload["bytes_copied"] == 50
    assert payload["files_copied"] == 3
    assert payload["progress"] == pytest.approx(0.25)
    assert payload["error"] is None


@pytest.mark.django_db
def test_operation_detail_uses_files_based_progress_when_bytes_total_is_zero():
    operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(),
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.RUNNING,
        bytes_total=0,
        files_total=8,
        bytes_copied=0,
        files_copied=2,
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.get(_operation_url(operation.operation_id))

    assert response.status_code == 200
    assert response.json()["progress"] == pytest.approx(0.25)


@pytest.mark.django_db
def test_operation_detail_returns_null_progress_when_no_totals():
    operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(),
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        bytes_total=None,
        files_total=None,
        bytes_copied=5,
        files_copied=1,
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.get(_operation_url(operation.operation_id))

    assert response.status_code == 200
    assert response.json()["progress"] is None


@pytest.mark.django_db
def test_operation_detail_returns_error_payload_for_failed_operation():
    operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(),
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
        error_message="AzCopy job failed.",
        error_details=json.dumps(
            {"code": "AZCOPY_FAILURE", "message": "copy failed"},
            sort_keys=True,
        ),
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.get(_operation_url(operation.operation_id))
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] == {
        "title": "AzCopy job failed.",
        "message": "AzCopy job failed.",
        "details": {"code": "AZCOPY_FAILURE", "message": "copy failed"},
        "code": "AZCOPY_FAILURE",
    }
