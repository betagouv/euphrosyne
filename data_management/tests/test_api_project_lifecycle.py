from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)
from euphro_auth.jwt.tokens import EuphroToolsAPIToken
from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from lab.tests.factories import ParticipationFactory

from .factories import ProjectDataFactory


def _backend_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token or EuphroToolsAPIToken.for_euphrosyne()}"}


@pytest.mark.django_db
def test_project_lifecycle_api_returns_project_lifecycle_snapshot_for_lab_admin():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_at=timezone.now(),
    )

    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        f"/api/data-management/projects/{project_data.project.slug}/lifecycle"
    )

    assert response.status_code == 200
    assert response.json() == {
        "lifecycle_state": LifecycleState.COOLING,
        "last_operation_id": str(operation.operation_id),
        "last_operation_type": LifecycleOperationType.COOL,
    }


@pytest.mark.django_db
def test_project_lifecycle_api_returns_project_lifecycle_snapshot_for_backend_token():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOLING)
    operation = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_at=timezone.now(),
    )

    response = Client().get(
        f"/api/data-management/projects/{project_data.project.slug}/lifecycle",
        headers=_backend_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "lifecycle_state": LifecycleState.COOLING,
        "last_operation_id": str(operation.operation_id),
        "last_operation_type": LifecycleOperationType.COOL,
    }


@pytest.mark.django_db
def test_project_lifecycle_api_returns_project_lifecycle_snapshot_for_project_member():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    member = StaffUserFactory()
    ParticipationFactory(project=project_data.project, user=member)
    client = Client()
    client.force_login(member)

    response = client.get(
        f"/api/data-management/projects/{project_data.project.slug}/lifecycle"
    )

    assert response.status_code == 200
    assert response.json() == {
        "lifecycle_state": LifecycleState.HOT,
        "last_operation_id": None,
        "last_operation_type": None,
    }


@pytest.mark.django_db
def test_project_lifecycle_api_is_forbidden_for_non_member_staff_users():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    client = Client()
    client.force_login(StaffUserFactory())

    response = client.get(
        f"/api/data-management/projects/{project_data.project.slug}/lifecycle"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_project_lifecycle_api_rejects_non_backend_jwt_user():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    token = EuphroToolsAPIToken.for_user(StaffUserFactory())

    response = Client().get(
        f"/api/data-management/projects/{project_data.project.slug}/lifecycle",
        headers=_backend_headers(str(token)),
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_project_lifecycle_api_returns_not_found_for_unknown_project_slug():
    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(f"/api/data-management/projects/{uuid.uuid4()}/lifecycle")

    assert response.status_code == 404


@pytest.mark.django_db
def test_project_lifecycle_api_returns_running_operation_as_last_operation():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.RESTORING)
    base_time = timezone.now()
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
        started_at=base_time - timedelta(minutes=10),
        finished_at=base_time - timedelta(minutes=5),
    )
    running_restore = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.RUNNING,
        started_at=base_time,
        finished_at=None,
    )

    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        f"/api/data-management/projects/{project_data.project.slug}/lifecycle"
    )

    assert response.status_code == 200
    assert response.json() == {
        "lifecycle_state": LifecycleState.RESTORING,
        "last_operation_id": str(running_restore.operation_id),
        "last_operation_type": LifecycleOperationType.RESTORE,
    }
