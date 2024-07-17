from unittest import mock

import pytest
from django.test import Client

from lab.tests import factories

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
            "runs": [factories.NotEmbargoedRun().id],
        }
        client = Client()
        response = client.post("/api/data-request/", data=data)

        assert response.status_code == 201


@pytest.mark.django_db
def test_create_view_with_embargoed_run():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        data = {
            **BASE_BODY_DATA,
            "runs": [factories.RunFactory().id],
        }
        client = Client()
        response = client.post("/api/data-request/", data=data)

        assert response.status_code == 400
        assert "runs" in response.json()
