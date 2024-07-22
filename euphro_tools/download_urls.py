"""Everything related to getting signed download link from euphro tools."""

import os
from datetime import datetime
from typing import Literal

import requests

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

from .exceptions import EuphroToolsException
from .utils import get_run_data_path

DataType = Literal["raw_data", "processed_data"]


def generate_download_url(
    project_slug: str, run_label: str, data_type: DataType, token: str
) -> str:
    """Generate a download URL for a run's data.
    Token can be obtained by calling fetch_token_for_run_data function."""
    return (
        os.environ["EUPHROSYNE_TOOLS_API_URL"]
        + "/data/run-data-zip"
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
    token_url = (
        os.environ["EUPHROSYNE_TOOLS_API_URL"]
        + f"/data/{project_slug}/token"
        + f"?path={get_run_data_path(project_slug, run_label, data_type)}"
    )
    if data_request_id:
        token_url += f"&data_request={data_request_id}"
    bearer_token = EuphroToolsAPIToken.for_euphrosyne().access_token
    try:
        request = requests.get(
            token_url,
            timeout=5,
            headers={"Authorization": f"Bearer {bearer_token}"},
        )
        request.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError) as error:
        raise EuphroToolsException from error
    return request.json()["token"]
