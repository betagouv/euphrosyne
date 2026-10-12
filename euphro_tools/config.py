import re
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

INVALID_URL_CHARS = re.compile(r"[?#\\\x00-\x20\x7f]")


def validate_tools_api_url(base_url: str) -> str:
    """Validate the deployment-controlled URL when Django loads its settings."""
    error_message = "Invalid EUPHROSYNE_TOOLS_API_URL"
    try:
        parsed = urlsplit(base_url)
    except ValueError:
        raise ImproperlyConfigured(error_message) from None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or INVALID_URL_CHARS.search(base_url)
    ):
        raise ImproperlyConfigured(error_message)
    return base_url
