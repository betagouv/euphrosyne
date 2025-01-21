import logging
from unittest import mock

import pytest

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
    patcher.start()
    yield
    patcher.stop()
