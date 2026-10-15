import logging
import re
from typing import Optional
from urllib.parse import quote

import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

logger = logging.getLogger(__name__)
INVALID_SEGMENT_CHARS = re.compile(r"[/\\\x00-\x1f\x7f]")


class RenameFailedError(Exception):
    pass


def _directory_url(*segments: str) -> str:
    """Keep directory names as literal segments of the configured Tools API URL."""
    for segment in segments:
        if segment in {"", ".", ".."} or INVALID_SEGMENT_CHARS.search(segment):
            raise ValueError("Invalid Tools API directory path segment")
    base_url = settings.EUPHROSYNE_TOOLS_API_URL.rstrip("/")
    return f"{base_url}/{'/'.join(quote(segment, safe='') for segment in segments)}"


def _make_request(
    url: str, raise_on_error: bool = False
) -> Optional[requests.Response]:
    """Make an authorized request to Euphrosyne tools API."""
    token = EuphroToolsAPIToken.for_euphrosyne().access_token
    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
            allow_redirects=False,
        )
        if 300 <= response.status_code < 400:
            raise requests.HTTPError(
                "Euphrosyne Tools API redirects are not allowed.", response=response
            )
        return response
    except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as error:
        if raise_on_error:
            raise error
        logger.error(
            "Error making call to Euphrosyne Tools API.\nURL: %s\nReason: %s",
            url,
            str(error),
        )
    return None


def initialize_project_directory(project_slug: str):
    response = _make_request(_directory_url("data", project_slug, "init"))
    if response is not None and not response.ok:
        logger.error(
            "Could not init project %s directory. %s: %s",
            project_slug,
            response.status_code,
            response.text,
        )


def initialize_run_directory(project_slug: str, run_name: str):
    response = _make_request(
        _directory_url("data", project_slug, "runs", run_name, "init")
    )
    if response is not None and not response.ok:
        logger.error(
            "Could not init run %s directory of project %s. %s: %s",
            run_name,
            project_slug,
            response.status_code,
            response.text,
        )


def rename_run_directory(project_slug: str, run_name: str, new_run_name: str):
    response = _make_request(
        _directory_url("data", project_slug, "runs", run_name, "rename", new_run_name)
    )
    if response is not None and not response.ok:
        logger.error(
            "Could not update run directory name from %s to %s of project %s. %s: %s",
            run_name,
            new_run_name,
            project_slug,
            response.status_code,
            response.text,
        )


def rename_project_directory(project_slug: str, new_project_slug: str):
    base_error_message = "Could not update project directory name from %s to %s. %s"
    error = ""
    try:
        response = _make_request(
            _directory_url("data", project_slug, "rename", new_project_slug),
            raise_on_error=True,
        )
    except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
        logger.error(
            base_error_message,
            project_slug,
            new_project_slug,
            str(e),
        )
        raise RenameFailedError(_("Euphro tools is not available.")) from e
    if response is not None and not response.ok:
        error = f"{response.status_code}: {response.text}"
        logger.error(
            base_error_message,
            project_slug,
            new_project_slug,
            str(error),
        )
        raise RenameFailedError(response.text)
