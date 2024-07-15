from unittest import mock

import pytest
from django.test import Client

from lab.tests import factories


@pytest.mark.django_db
def test_create_view():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        data = {
            "user_email": "dev@witold.fr",
            "user_first_name": "Dev",
            "user_last_name": "Witold",
            "user_institution": "Witold Institute of Technology",
            "description": "I need this data for my research.",
            "runs": [factories.RunFactory().id],
        }
        client = Client()
        response = client.post("/api/data-request/", data=data)

        assert response.status_code == 201
