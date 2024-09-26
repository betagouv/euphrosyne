import logging
import os
from typing import Optional

import requests
from django.utils.translation import gettext_lazy as _

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

logger = logging.getLogger(__name__)


class RenameFailedError(Exception):
    pass


def _make_request(
    url: str, raise_on_error: bool = False
) -> Optional[requests.Response]:
    """Make an authorized request to Euphrosyne tools API."""
    token = EuphroToolsAPIToken.for_euphrosyne().access_token
    try:
        return requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
    except (requests.Timeout, requests.ConnectionError) as error:
        if raise_on_error:
            raise error
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


def rename_project_directory(project_name: str, new_project_name: str):
    base_url = os.environ["EUPHROSYNE_TOOLS_API_URL"]
    base_error_message = "Could not update project directory name from %s to %s. %s"
    error = ""
    try:
        response = _make_request(
            f"{base_url}/data/{project_name}/rename/{new_project_name}",
            raise_on_error=True,
        )
    except (requests.Timeout, requests.ConnectionError) as e:
        logger.error(
            base_error_message,
            project_name,
            new_project_name,
            str(error),
        )
        raise RenameFailedError(_("Euphro tools is not available.")) from e
    if response is not None and not response.ok:
        error = f"{response.status_code}: {response.text}"
        logger.error(
            base_error_message,
            project_name,
            new_project_name,
            str(error),
        )
        raise RenameFailedError(response.text)
