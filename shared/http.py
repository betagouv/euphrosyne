"""HTTP downloads limited to explicitly trusted origins, without redirects."""

from collections.abc import Collection
from urllib.parse import urlsplit

import requests


class DownloadError(Exception):
    """Safe error that contains neither the download URL nor its credentials."""


def _origin(url: str) -> tuple[str, str, int]:
    # Reject characters that URL parsers may strip or interpret differently.
    if any(ord(char) <= 32 or ord(char) == 127 for char in url) or "\\" in url:
        raise ValueError
    parts = urlsplit(url)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or "#" in url
    ):
        raise ValueError
    if any(
        char not in "abcdefghijklmnopqrstuvwxyz0123456789.-:[]"
        for char in parts.netloc.lower()
    ):
        raise ValueError
    if parts.netloc.endswith(":"):
        raise ValueError
    port = (
        parts.port
        if parts.port is not None
        else (443 if parts.scheme == "https" else 80)
    )
    if port == 0:
        raise ValueError
    return parts.scheme, parts.hostname.lower(), port


def validate_download_url(url: str, allowed_origins: Collection[str]) -> None:
    """Compare full scheme/host/effective-port tuples; never match host suffixes."""
    try:
        origin = _origin(url)
        if origin not in {_origin(allowed) for allowed in allowed_origins}:
            raise ValueError
    except ValueError:
        raise DownloadError("Download origin is not allowed.") from None


def get_download_response(
    url: str,
    *,
    allowed_origins: Collection[str],
    timeout: int,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    """Validate before sending credentials and reject every non-success response."""
    validate_download_url(url, allowed_origins)
    try:
        response = requests.get(
            url, timeout=timeout, headers=headers, allow_redirects=False
        )
    except requests.RequestException:
        raise DownloadError("Download request failed.") from None
    if not 200 <= response.status_code < 300:
        response.close()
        raise DownloadError("Download did not return a successful response.")
    return response
