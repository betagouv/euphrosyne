import logging
import os
from typing import Optional

import requests

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

logger = logging.getLogger(__name__)


def _make_request(url: str) -> Optional[requests.Response]:
    """Make an authorized request to Euphrosyne tools API."""
    token = EuphroToolsAPIToken.for_euphrosyne().access_token
    try:
        return requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
    except (requests.Timeout, requests.ConnectionError) as error:
        logger.error(
            "Error making call to Euphrosyne Tools API.\nURL: %s\nReason: %s",
            url,
            str(error),
        )
    return None


def initialize_project_directory(project_name: str):
    base_url = os.environ["EUPHROSYNE_TOOLS_API_URL"]
    response = _make_request(f"{base_url}/data/{project_name}/init")
    if response is not None and not response.ok:
        logger.error(
            "Could not init project %s directory. %s: %s",
            project_name,
            response.status_code,
            response.text,
        )


def initialize_run_directory(project_name: str, run_name: str):
    base_url = os.environ["EUPHROSYNE_TOOLS_API_URL"]
    response = _make_request(f"{base_url}/data/{project_name}/runs/{run_name}/init")
    if response is not None and not response.ok:
        logger.error(
            "Could not init run %s directory of project %s. %s: %s",
            run_name,
            project_name,
            response.status_code,
            response.text,
        )


def rename_run_directory(project_name: str, run_name: str, new_run_name: str):
    base_url = os.environ["EUPHROSYNE_TOOLS_API_URL"]
    response = _make_request(
        f"{base_url}/data/{project_name}/runs/{run_name}/rename/{new_run_name}"
    )
    if response is not None and not response.ok:
        logger.error(
            "Could not update run directory name from %s to %s of project %s. %s: %s",
            run_name,
            new_run_name,
            project_name,
            response.status_code,
            response.text,
        )
