"""Everything related to getting signed download link from euphro tools."""

import typing
from datetime import datetime
from urllib.parse import quote, urlencode

import requests

from shared.http import DownloadError, get_download_response

from .exceptions import EuphroToolsException
from .utils import build_tools_api_url, get_run_data_path, get_tools_api_auth_header

DataType = typing.Literal["raw_data", "processed_data"]


def generate_download_url(
    project_slug: str, run_label: str, data_type: DataType, token: str
) -> str:
    """Generate a download URL for a run's data.
    Token can be obtained by calling fetch_token_for_run_data function."""
    query = urlencode(
        {
            "token": token,
            "path": get_run_data_path(project_slug, run_label, data_type),
        }
    )
    return f"{build_tools_api_url('/data/run-data-zip')}?{query}"


def fetch_token_for_run_data(
    project_slug: str,
    run_label: str,
    data_type: DataType,
    expiration: datetime | None = None,
    data_request_id: str | None = None,
) -> str:
    token_url = build_tools_api_url(f"/data/{project_slug}/token")
    params = {"path": get_run_data_path(project_slug, run_label, data_type)}
    if expiration:
        params["expiration"] = expiration.isoformat()
    if data_request_id:
        params["data_request"] = data_request_id
    try:
        request = requests.get(
            token_url,
            params=params,
            timeout=5,
            headers=get_tools_api_auth_header(),
        )
        request.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError) as error:
        raise EuphroToolsException from error
    return request.json()["token"]


class GetUrlAndTokenForProjectImagesResponse(typing.TypedDict):
    base_url: str
    token: str


def get_storage_info_for_project_images(
    project_slug: str,
) -> GetUrlAndTokenForProjectImagesResponse:
    """Get a download URL and token for a project's images."""
    url = build_tools_api_url(
        f"/images/projects/{quote(project_slug, safe='')}/signed-url"
    )
    try:
        request = get_download_response(
            url,
            allowed_origins=[build_tools_api_url("/")],
            timeout=5,
            headers=get_tools_api_auth_header(),
        )
        try:
            data = request.json()
        finally:
            request.close()
    except (DownloadError, ValueError):
        raise EuphroToolsException from None
    if not isinstance(data, dict) or not all(
        isinstance(data.get(key), str) for key in ("base_url", "token")
    ):
        raise EuphroToolsException
    return typing.cast(GetUrlAndTokenForProjectImagesResponse, data)
