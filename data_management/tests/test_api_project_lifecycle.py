from __future__ import annotations

import uuid

import pytest
from django.test import Client
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)
from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory

from .factories import ProjectDataFactory


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
def test_project_lifecycle_api_is_forbidden_for_non_lab_admin_users():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    client = Client()
    client.force_login(StaffUserFactory())

    response = client.get(
        f"/api/data-management/projects/{project_data.project.slug}/lifecycle"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_project_lifecycle_api_returns_not_found_for_unknown_project_slug():
    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(f"/api/data-management/projects/{uuid.uuid4()}/lifecycle")

    assert response.status_code == 404
