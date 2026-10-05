from unittest import mock

import pytest
import requests

from shared.http import DownloadError, get_download_response, validate_download_url

ORIGIN = "https://account.blob.core.windows.net"


@pytest.mark.parametrize(
    "url",
    [
        f"{ORIGIN}/image.jpg?sig=test-token",
        "https://ACCOUNT.blob.core.windows.net:443/image.jpg",
    ],
)
def test_exact_origin_allows_signed_url_and_default_port(url):
    validate_download_url(url, [ORIGIN])


@pytest.mark.parametrize(
    "url",
    [
        "http://account.blob.core.windows.net/image.jpg",
        "https://account.blob.core.windows.net:444/image.jpg",
        "https://other.blob.core.windows.net/image.jpg",
        "https://account.blob.core.windows.net.evil.example/image.jpg",
        "https://evilaccount.blob.core.windows.net/image.jpg",
        "https://account.blob.core.windows.net./image.jpg",
        "https://account.blob.core.windows.net@localhost/image.jpg",
        "https://user:password@account.blob.core.windows.net/image.jpg",
        "https://account.blob.core.windows.net%2f@localhost/image.jpg",
        "https://account.blob.core.windows.net\\@localhost/image.jpg",
        "https://127.0.0.1/image.jpg",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/image.jpg",
        "http://localhost/image.jpg",
        "http://[::1]/image.jpg",
        "file:///etc/passwd",
        "ftp://account.blob.core.windows.net/image.jpg",
        "//account.blob.core.windows.net/image.jpg",
        "/image.jpg",
        "https://account.blob.core.windows.net:invalid/image.jpg",
        "https://account.blob.core.windows.net:65536/image.jpg",
        "https://account.blob.core.windows.net:0/image.jpg",
        "https://account.blob.core.windows.net:/image.jpg",
        "https://[invalid/image.jpg",
        f"{ORIGIN}/image.jpg#fragment",
        f"{ORIGIN}/image.jpg#",
        f" {ORIGIN}/image.jpg",
        f"{ORIGIN}\n/image.jpg",
        f"{ORIGIN}\t/image.jpg",
        f"{ORIGIN}/image\x7f.jpg",
        "https://account.blob.core.windows.net%00/image.jpg",
    ],
)
@mock.patch("shared.http.requests.get")
def test_disallowed_url_is_rejected_before_request(mock_get, url):
    with pytest.raises(DownloadError):
        get_download_response(url, allowed_origins=[ORIGIN], timeout=5)
    mock_get.assert_not_called()


@pytest.mark.parametrize("origin", ["", "https://[broken", "file:///tmp/images"])
@mock.patch("shared.http.requests.get")
def test_invalid_origin_configuration_fails_closed(mock_get, origin):
    with pytest.raises(DownloadError):
        get_download_response(ORIGIN, allowed_origins=[origin], timeout=5)
    mock_get.assert_not_called()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize(
    "location",
    [
        "http://169.254.169.254/latest/meta-data/",
        "https://evil.example/image.jpg",
        f"{ORIGIN}/other.jpg",
        "/other.jpg",
    ],
)
@mock.patch("shared.http.requests.get")
def test_redirect_is_not_followed(mock_get, status, location):
    response = mock.Mock(status_code=status, headers={"Location": location})
    mock_get.return_value = response
    with pytest.raises(DownloadError):
        get_download_response(ORIGIN, allowed_origins=[ORIGIN], timeout=5)
    mock_get.assert_called_once_with(
        ORIGIN, timeout=5, headers=None, allow_redirects=False
    )
    response.close.assert_called_once()


@pytest.mark.parametrize("status", [304, 400, 403, 404, 500])
@mock.patch("shared.http.requests.get")
def test_unsuccessful_response_is_closed(mock_get, status):
    response = mock.Mock(status_code=status)
    mock_get.return_value = response
    with pytest.raises(DownloadError):
        get_download_response(ORIGIN, allowed_origins=[ORIGIN], timeout=5)
    response.close.assert_called_once()


@pytest.mark.parametrize(
    "error", [requests.Timeout, requests.ConnectionError, requests.HTTPError]
)
@mock.patch("shared.http.requests.get")
def test_network_error_does_not_expose_signed_url(mock_get, error):
    mock_get.side_effect = error(f"{ORIGIN}/image.jpg?sig=private-test-token")
    with pytest.raises(DownloadError) as exc:
        get_download_response(ORIGIN, allowed_origins=[ORIGIN], timeout=5)
    assert "private-test-token" not in str(exc.value)
    assert exc.value.__suppress_context__
