"""Everything related to getting signed download link from euphro tools."""

import typing
from datetime import datetime

import requests

from .exceptions import EuphroToolsException
from .utils import build_tools_api_url, get_run_data_path, get_tools_api_auth_header

DataType = typing.Literal["raw_data", "processed_data"]


def generate_download_url(
    project_slug: str, run_label: str, data_type: DataType, token: str
) -> str:
    """Generate a download URL for a run's data.
    Token can be obtained by calling fetch_token_for_run_data function."""
    return (
        build_tools_api_url("/data/run-data-zip")
        + f"?token={token}&path={get_run_data_path(project_slug, run_label, data_type)}"
    )


def fetch_token_for_run_data(
    project_slug: str,
    run_label: str,
    data_type: DataType,
    expiration: datetime | None = None,
    data_request_id: str | None = None,
) -> str:
    query_params = f"?path={get_run_data_path(project_slug, run_label, data_type)}"
    if expiration:
        query_params += f"&expiration={expiration.isoformat()}"
    token_url = build_tools_api_url(f"/data/{project_slug}/token") + query_params
    if data_request_id:
        token_url += f"&data_request={data_request_id}"
    try:
        request = requests.get(
            token_url,
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
    url = build_tools_api_url(f"/images/projects/{project_slug}/signed-url")
    try:
        request = requests.get(
            url,
            timeout=5,
            headers=get_tools_api_auth_header(),
        )
        request.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError) as error:
        raise EuphroToolsException from error
    return request.json()
