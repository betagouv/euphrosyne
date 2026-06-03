from unittest import mock

import pytest
from django.test import Client, override_settings

from euphro_auth.jwt.tokens import EuphroToolsAPIToken
from lab.tests import factories as lab_factories

from . import factories

ALLOWED_ORIGIN = "https://euphrosyne-digilab-production.osc-secnum-fr1.scalingo.io"

BASE_BODY_DATA = {
    "user_email": "dev@witold.fr",
    "user_first_name": "Dev",
    "user_last_name": "Witold",
    "user_institution": "Witold Institute of Technology",
    "description": "I need this data for my research.",
}


def _valid_data_request_payload():
    return {
        **BASE_BODY_DATA,
        "runs": [lab_factories.NotEmbargoedRun().id],
    }


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_create_view():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        data = _valid_data_request_payload()
        client = Client()
        response = client.post(
            "/api/data-request/",
            data=data,
            headers={"Origin": ALLOWED_ORIGIN},
        )

        assert response.status_code == 201


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_create_view_with_embargoed_run():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        data = {
            **BASE_BODY_DATA,
            "runs": [lab_factories.RunFactory().id],
        }
        client = Client()
        response = client.post(
            "/api/data-request/",
            data=data,
            headers={"Origin": ALLOWED_ORIGIN},
        )

        assert response.status_code == 400
        assert "runs" in response.json()


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[])
def test_create_view_remains_permissive_without_configured_origins():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        response = Client().post(
            "/api/data-request/", data=_valid_data_request_payload()
        )

        assert response.status_code == 201


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_create_view_without_origin_is_forbidden():
    response = Client().post("/api/data-request/", data=_valid_data_request_payload())

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_create_view_with_not_allowed_origin_is_forbidden():
    response = Client().post(
        "/api/data-request/",
        data=_valid_data_request_payload(),
        headers={"Origin": "https://example.com"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[f"{ALLOWED_ORIGIN}/"])
def test_create_view_allows_configured_origin_with_trailing_slash():
    with mock.patch("data_request.api_views.send_data_request_created_email"):
        response = Client().post(
            "/api/data-request/",
            data=_valid_data_request_payload(),
            headers={"Origin": ALLOWED_ORIGIN},
        )

        assert response.status_code == 201


@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_create_view_options_is_not_blocked_by_origin_permission():
    response = Client().options("/api/data-request/")

    assert response.status_code != 403


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_create_view_logs_warning_when_origin_is_rejected(caplog):
    response = Client().post("/api/data-request/", data=_valid_data_request_payload())

    assert response.status_code == 403
    assert (
        "Rejected data request submission because Origin is not allowed" in caplog.text
    )
    assert "/api/data-request/" in caplog.text
    assert BASE_BODY_DATA["user_email"] not in caplog.text


@pytest.mark.django_db
@override_settings(DATA_REQUEST_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
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
