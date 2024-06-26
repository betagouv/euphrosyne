from unittest import mock

import pytest


@pytest.fixture(
    autouse=True,
    scope="package",
)
def elasticsearch_client():
    patcher = mock.patch("opensearchpy.OpenSearch")
    yield patcher.start()
    patcher.stop()
