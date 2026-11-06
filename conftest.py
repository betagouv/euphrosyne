import logging
from types import SimpleNamespace
from unittest import mock

import pytest
from django.test import Client

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from euphrosyne.tests.openapi_request_validation import set_validation_enabled
from lab.tests.factories import (
    ParticipationFactory,
    ProjectWithLeaderFactory,
    RunFactory,
)

logging.getLogger("faker").setLevel(logging.WARNING)

OPENAPI_INVALID_REQUEST_MARKER = "openapi_invalid_request"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        f"{OPENAPI_INVALID_REQUEST_MARKER}: the test sends /api/ requests that do "
        "not conform to the OpenAPI schema on purpose (they would be rejected by "
        "the WAF); skip their validation.",
    )


@pytest.fixture(autouse=True)
def validate_api_requests_against_openapi_schema(request, settings):
    """Fail on /api/ requests made with the test client that do not conform to
    the OpenAPI schema. See euphrosyne/tests/openapi_request_validation.py."""
    settings.MIDDLEWARE = [
        *settings.MIDDLEWARE,
        "euphrosyne.tests.openapi_request_validation."
        "OpenAPIRequestValidationMiddleware",
    ]
    set_validation_enabled(
        request.node.get_closest_marker(OPENAPI_INVALID_REQUEST_MARKER) is None
    )
    yield
    set_validation_enabled(False)


@pytest.fixture(autouse=True)
def setup_django_conf(monkeypatch: pytest.MonkeyPatch, settings):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "https://tools")
    settings.EUPHROSYNE_TOOLS_API_URL = "https://tools"
    settings.FORCE_LAST_CGU_ACCEPTANCE_DT = None


@pytest.fixture(autouse=True, scope="session")
def mock_requests():
    patcher = mock.patch.multiple(
        "requests",
        post=mock.DEFAULT,
        get=mock.DEFAULT,
        put=mock.DEFAULT,
        delete=mock.DEFAULT,
        patch=mock.DEFAULT,
    )
    mocks = patcher.start()
    mocks["post"].return_value.status_code = 200
    yield
    patcher.stop()


@pytest.fixture(
    params=[
        "anonymous",
        "non_staff",
        "unrelated_staff",
        "non_staff_member",
        "member",
        "leader",
        "lab_admin",
        "superuser",
    ]
)
def project_api_context(request, db):  # pylint: disable=unused-argument
    """Exercise project API routes with real sessions and distinct project roles."""
    project = ProjectWithLeaderFactory()
    role = request.param
    if role == "anonymous":
        user = None
    elif role == "leader":
        user = project.leader.user
    elif role == "lab_admin":
        user = LabAdminUserFactory()
    else:
        user = StaffUserFactory(
            is_staff=role not in {"non_staff", "non_staff_member"},
            is_superuser=role == "superuser",
        )
        if role in {"member", "non_staff_member"}:
            ParticipationFactory(project=project, user=user)

    client = Client()
    if user:
        client.force_login(user)
    return SimpleNamespace(
        role=role,
        user=user,
        client=client,
        project=project,
        run=RunFactory(project=project),
        can_access_project=role in {"member", "leader", "lab_admin", "superuser"},
        can_manage_participations=role in {"leader", "lab_admin", "superuser"},
    )
