from __future__ import annotations

from urllib.parse import quote

import requests

from .utils import build_tools_api_url, get_tools_api_auth_header


def post_cool_project(
    *,
    project_slug: str,
    operation_id: str,
    timeout: int,
) -> requests.Response:
    project_part = quote(project_slug, safe="")
    url = build_tools_api_url(
        f"data/projects/{project_part}/cool"
        f"?operation_id={quote(operation_id, safe='')}"
    )
    return requests.post(
        url,
        timeout=timeout,
        headers=get_tools_api_auth_header(),
    )


def post_restore_project(
    *,
    project_slug: str,
    operation_id: str,
    timeout: int,
) -> requests.Response:
    project_part = quote(project_slug, safe="")
    url = build_tools_api_url(
        f"data/projects/{project_part}/restore"
        f"?operation_id={quote(operation_id, safe='')}"
    )
    return requests.post(
        url,
        timeout=timeout,
        headers=get_tools_api_auth_header(),
    )
