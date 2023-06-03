""" Tests API URLs -- pings each URL to check it is found. """

import pytest
from django.test import Client


@pytest.mark.parametrize(
    "path",
    ("/auth/token", "/auth/token/refresh", "/projects"),
)
def test_api_url(path: str):
    client = Client()
    response = client.get(f"/api/{path}")

    assert response.status_code != 404
