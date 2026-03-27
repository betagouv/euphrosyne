from __future__ import annotations

from unittest import mock

import pytest
import requests
from django.test import Client
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)
from euphro_auth.tests import factories as auth_factories
from lab.tests.factories import ProjectFactory

from .factories import ProjectDataFactory


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def _cool_url(project_id: int) -> str:
    return f"/api/data-management/projects/{project_id}/cool"


@pytest.mark.django_db
def test_cool_retry_requires_lab_admin():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
    )

    anon_response = Client().post(_cool_url(project_data.project_id))
    assert anon_response.status_code in {401, 403}

    staff_client = Client()
    staff_client.force_login(auth_factories.StaffUserFactory())
    staff_response = staff_client.post(_cool_url(project_data.project_id))
    assert staff_response.status_code == 403


@pytest.mark.django_db
def test_cool_from_hot_when_eligible_calls_tools_api_and_transitions_to_cooling():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    project_data.cooling_eligible_at = timezone.localdate() - timezone.timedelta(days=1)
    project_data.save(update_fields=["cooling_eligible_at"])
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch(
        "data_management.api_views.post_cool_project",
        return_value=DummyResponse(status_code=202),
    ) as cool_mock:
        response = client.post(_cool_url(project_data.project_id))

    project_data.refresh_from_db()
    payload = response.json()
    operation = LifecycleOperation.objects.get(operation_id=payload["operation_id"])

    assert response.status_code == 202
    assert payload["lifecycle_state"] == LifecycleState.COOLING
    assert operation.type == LifecycleOperationType.COOL
    assert operation.status == LifecycleOperationStatus.RUNNING
    assert project_data.lifecycle_state == LifecycleState.COOLING
    cool_mock.assert_called_once_with(
        project_slug=project_data.project.slug,
        operation_id=payload["operation_id"],
        timeout=10,
    )


@pytest.mark.django_db
def test_cool_from_hot_when_not_eligible_is_rejected():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.post(_cool_url(project_data.project_id))

    assert response.status_code == 400
    assert response.json()["lifecycle_state"] == LifecycleState.HOT


@pytest.mark.django_db
def test_cool_recreates_missing_project_data_with_for_project():
    project = ProjectFactory()
    project.project_data.delete()

    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    def create_project_data(_project):
        return ProjectData.objects.create(
            project=_project,
            cooling_eligible_at=timezone.now() - timezone.timedelta(days=1),
        )

    with mock.patch(
        "data_management.api_views.post_cool_project",
        return_value=DummyResponse(status_code=202),
    ) as cool_mock, mock.patch(
        "data_management.operations.ProjectData.for_project",
        side_effect=create_project_data,
    ) as for_project_mock:
        response = client.post(_cool_url(project.id))

    project_data = ProjectData.objects.get(project=project)
    payload = response.json()
    operation = LifecycleOperation.objects.get(operation_id=payload["operation_id"])

    assert response.status_code == 202
    assert payload["lifecycle_state"] == LifecycleState.COOLING
    assert project_data.lifecycle_state == LifecycleState.COOLING
    assert operation.project_data_id == project_data.pk
    for_project_mock.assert_called_once()
    cool_mock.assert_called_once_with(
        project_slug=project.slug,
        operation_id=payload["operation_id"],
        timeout=10,
    )


@pytest.mark.django_db
def test_cool_retry_rejects_when_last_operation_is_not_cool():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.FAILED,
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.post(_cool_url(project_data.project_id))

    assert response.status_code == 400
    assert response.json()["lifecycle_state"] == LifecycleState.ERROR
    assert LifecycleOperation.objects.count() == 1


@pytest.mark.django_db
def test_cool_retry_from_error_calls_tools_api_and_transitions_to_cooling():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch(
        "data_management.api_views.post_cool_project",
        return_value=DummyResponse(status_code=202),
    ) as cool_mock:
        response = client.post(_cool_url(project_data.project_id))

    project_data.refresh_from_db()
    payload = response.json()
    operation = LifecycleOperation.objects.get(operation_id=payload["operation_id"])

    assert response.status_code == 202
    assert payload["lifecycle_state"] == LifecycleState.COOLING
    assert operation.type == LifecycleOperationType.COOL
    assert operation.status == LifecycleOperationStatus.RUNNING
    assert project_data.lifecycle_state == LifecycleState.COOLING
    cool_mock.assert_called_once_with(
        project_slug=project_data.project.slug,
        operation_id=payload["operation_id"],
        timeout=10,
    )


@pytest.mark.django_db
def test_cool_retry_marks_operation_failed_when_tools_api_is_unavailable():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch(
        "data_management.api_views.post_cool_project",
        side_effect=requests.RequestException("boom"),
    ):
        response = client.post(_cool_url(project_data.project_id))

    project_data.refresh_from_db()
    payload = response.json()
    operation = LifecycleOperation.objects.get(operation_id=payload["operation_id"])

    assert response.status_code == 502
    assert operation.type == LifecycleOperationType.COOL
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "Tools API request failed."
    assert project_data.lifecycle_state == LifecycleState.ERROR


@pytest.mark.django_db
def test_cool_retry_marks_operation_failed_when_tools_api_rejects_request():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch(
        "data_management.api_views.post_cool_project",
        return_value=DummyResponse(status_code=500, text="server error"),
    ):
        response = client.post(_cool_url(project_data.project_id))

    project_data.refresh_from_db()
    payload = response.json()
    operation = LifecycleOperation.objects.get(operation_id=payload["operation_id"])

    assert response.status_code == 502
    assert operation.type == LifecycleOperationType.COOL
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "Tools API rejected cool request (500)."
    assert operation.error_details == "server error"
    assert project_data.lifecycle_state == LifecycleState.ERROR


@pytest.mark.django_db
@pytest.mark.parametrize(
    "active_status",
    [
        LifecycleOperationStatus.PENDING,
        LifecycleOperationStatus.RUNNING,
    ],
)
def test_cool_rejects_when_active_cool_operation_exists(active_status: str):
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.HOT)
    project_data.cooling_eligible_at = timezone.localdate() - timezone.timedelta(days=1)
    project_data.save(update_fields=["cooling_eligible_at"])
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=active_status,
        started_at=timezone.now(),
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch("data_management.api_views.post_cool_project") as cool_mock:
        response = client.post(_cool_url(project_data.project_id))

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Project already has an active lifecycle operation.",
        "lifecycle_state": LifecycleState.HOT,
    }
    assert LifecycleOperation.objects.count() == 1
    cool_mock.assert_not_called()


@pytest.mark.django_db
def test_cool_retry_rejects_when_another_active_operation_exists():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.PENDING,
    )
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
        started_at=timezone.now(),
    )
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch("data_management.api_views.post_cool_project") as cool_mock:
        response = client.post(_cool_url(project_data.project_id))

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Project already has an active lifecycle operation.",
        "lifecycle_state": LifecycleState.ERROR,
    }
    assert LifecycleOperation.objects.count() == 2
    cool_mock.assert_not_called()
