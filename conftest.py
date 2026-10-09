import logging
from types import SimpleNamespace
from unittest import mock

import pytest
from django.test import Client

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from lab.tests.factories import (
    ParticipationFactory,
    ProjectWithLeaderFactory,
    RunFactory,
)

logging.getLogger("faker").setLevel(logging.WARNING)


@pytest.fixture(autouse=True)
def setup_django_conf(monkeypatch: pytest.MonkeyPatch, settings):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "https://tools")
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
