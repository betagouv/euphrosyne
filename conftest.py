import logging
from unittest import mock

import pytest

logging.getLogger("faker").setLevel(logging.WARNING)


@pytest.fixture(autouse=True)
def setup_envs(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "https://tools")


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
