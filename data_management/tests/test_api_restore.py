from __future__ import annotations

from unittest import mock

import pytest
import requests
from django.test import Client

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)
from euphro_auth.tests import factories as auth_factories

from .factories import ProjectDataFactory


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def _restore_url(project_id: int) -> str:
    return f"/api/data-management/projects/{project_id}/restore"


@pytest.mark.django_db
def test_restore_requires_lab_admin():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOL)
    url = _restore_url(project_data.project_id)

    anon_response = Client().post(url, content_type="application/json")
    assert anon_response.status_code in {401, 403}

    staff_client = Client()
    staff_client.force_login(auth_factories.StaffUserFactory())
    staff_response = staff_client.post(url, content_type="application/json")
    assert staff_response.status_code == 403
    assert LifecycleOperation.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "state",
    [
        LifecycleState.HOT,
        LifecycleState.COOLING,
        LifecycleState.RESTORING,
    ],
)
def test_restore_rejects_invalid_states(state: LifecycleState):
    project_data = ProjectDataFactory(lifecycle_state=state)
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    response = client.post(
        _restore_url(project_data.project_id), content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json()["lifecycle_state"] == state
    assert LifecycleOperation.objects.count() == 0


@pytest.mark.django_db
def test_restore_from_cool_creates_operation_and_calls_tools_api():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOL)
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch(
        "data_management.api_views.post_restore_project",
        return_value=DummyResponse(status_code=202),
    ) as restore_mock:
        response = client.post(
            _restore_url(project_data.project_id),
            content_type="application/json",
        )

    project_data.refresh_from_db()
    payload = response.json()
    operation = LifecycleOperation.objects.get(operation_id=payload["operation_id"])

    assert response.status_code == 202
    assert payload["lifecycle_state"] == LifecycleState.RESTORING
    assert operation.type == LifecycleOperationType.RESTORE
    assert operation.status == LifecycleOperationStatus.RUNNING
    assert project_data.lifecycle_state == LifecycleState.RESTORING
    restore_mock.assert_called_once_with(
        project_slug=project_data.project.slug,
        timeout=10,
    )


@pytest.mark.django_db
def test_restore_marks_failed_when_tools_api_is_unavailable():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOL)
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch(
        "data_management.api_views.post_restore_project",
        side_effect=requests.RequestException("boom"),
    ):
        response = client.post(
            _restore_url(project_data.project_id),
            content_type="application/json",
        )

    project_data.refresh_from_db()
    operation = LifecycleOperation.objects.get()
    payload = response.json()

    assert response.status_code == 502
    assert payload["operation_id"] == str(operation.operation_id)
    assert operation.type == LifecycleOperationType.RESTORE
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "Tools API request failed."
    assert project_data.lifecycle_state == LifecycleState.ERROR


@pytest.mark.django_db
def test_restore_marks_failed_when_tools_api_rejects_request():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.COOL)
    client = Client()
    client.force_login(auth_factories.LabAdminUserFactory())

    with mock.patch(
        "data_management.api_views.post_restore_project",
        return_value=DummyResponse(status_code=500, text="server error"),
    ):
        response = client.post(
            _restore_url(project_data.project_id),
            content_type="application/json",
        )

    project_data.refresh_from_db()
    operation = LifecycleOperation.objects.get()
    payload = response.json()

    assert response.status_code == 502
    assert payload["operation_id"] == str(operation.operation_id)
    assert operation.type == LifecycleOperationType.RESTORE
    assert operation.status == LifecycleOperationStatus.FAILED
    assert operation.error_message == "Tools API rejected restore request (500)."
    assert operation.error_details == "server error"
    assert project_data.lifecycle_state == LifecycleState.ERROR
