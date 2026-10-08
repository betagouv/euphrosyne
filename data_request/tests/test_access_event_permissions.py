import pytest
from django.test import Client
from rest_framework_simplejwt.tokens import AccessToken

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

from .factories import DataRequestFactory


def test_access_event_rejects_user_sessions(project_api_context):
    context = project_api_context
    data_request = DataRequestFactory()
    response = context.client.post(
        "/api/data-request/access-event",
        {"data_request": data_request.id, "path": "test/path"},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert not data_request.data_access_events.exists()


def test_access_event_rejects_user_jwt(project_api_context):
    context = project_api_context
    if context.user is None:
        return
    data_request = DataRequestFactory()
    token = AccessToken.for_user(context.user)
    response = Client().post(
        "/api/data-request/access-event",
        {"data_request": data_request.id, "path": "test/path"},
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert not data_request.data_access_events.exists()


@pytest.mark.django_db
def test_access_event_accepts_backend_jwt():
    data_request = DataRequestFactory()
    token = EuphroToolsAPIToken.for_euphrosyne()
    response = Client().post(
        "/api/data-request/access-event",
        {"data_request": data_request.id, "path": "test/path"},
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert data_request.data_access_events.get().path == "test/path"
