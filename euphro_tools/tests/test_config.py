import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from ..config import validate_tools_api_url


@pytest.mark.parametrize(
    "base_url",
    [
        "http://localhost:8001",
        "https://tools.example",
        "https://tools.example/api/",
        "https://[::1]:8001/api",
    ],
)
def test_tools_api_url_accepts_existing_deployment_formats(base_url):
    assert validate_tools_api_url(base_url) == base_url


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        "//evil.example",
        "file:///tmp/tools",
        "https:///api",
        "https://user:password@tools.example",
        "https://tools.example?query",
        "https://tools.example#fragment",
        "https://tools.example\\evil",
        "https://tools.example/\napi",
        "https://tools.example/ api",
        "https://tools.example/\x00api",
        "https://tools.example/\x7fapi",
        "https://[invalid",
    ],
)
def test_invalid_tools_api_url_is_a_configuration_error(base_url):
    with pytest.raises(ImproperlyConfigured, match="Invalid EUPHROSYNE_TOOLS_API_URL"):
        validate_tools_api_url(base_url)


def test_invalid_tools_api_url_prevents_django_startup():
    result = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        cwd=Path(__file__).resolve().parents[2],
        env={
            "DJANGO_SETTINGS_MODULE": "euphrosyne.settings",
            "EUPHROSYNE_TOOLS_API_URL": "https://tools.example?query",
            "PYTHONDONTWRITEBYTECODE": "1",
            "SENTRY_DSN": "",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode != 0
    assert "ImproperlyConfigured: Invalid EUPHROSYNE_TOOLS_API_URL" in result.stderr
    assert "https://tools.example?query" not in result.stderr
