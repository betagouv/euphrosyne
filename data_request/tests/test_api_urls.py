from unittest import mock

import pytest
from django.test import Client

from euphro_auth.jwt.tokens import EuphroToolsAPIToken
from lab.tests import factories as lab_factories

from . import factories

BASE_BODY_DATA = {
    "user_email": "dev@witold.fr",
    "user_first_name": "Dev",
    "user_last_name": "Witold",
    "user_institution": "Witold Institute of Technology",
    "description": "I need this data for my research.",
}


@pytest.mark.django_db
def test_create_view():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        data = {
            **BASE_BODY_DATA,
            "runs": [lab_factories.NotEmbargoedRun().id],
        }
        client = Client()
        response = client.post("/api/data-request/", data=data)

        assert response.status_code == 201


@pytest.mark.django_db
def test_create_view_with_embargoed_run():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        data = {
            **BASE_BODY_DATA,
            "runs": [lab_factories.RunFactory().id],
        }
        client = Client()
        response = client.post("/api/data-request/", data=data)

        assert response.status_code == 400
        assert "runs" in response.json()


@pytest.mark.django_db
def test_data_access_event_create():
    data_request = factories.DataRequestFactory()
    token = EuphroToolsAPIToken.for_euphrosyne()
    data = {
        "data_request": data_request.id,
        "path": "path/to/data",
    }

    response = Client().post(
        "/api/data-request/access-event",
        data=data,
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert response.status_code == 201
    assert data_request.data_access_events.count() == 1
