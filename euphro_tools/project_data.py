from __future__ import annotations

from urllib.parse import quote

import requests

from .utils import build_tools_api_url, get_tools_api_auth_header


def _build_project_cool_url(project_slug: str) -> str:
    project_part = quote(project_slug, safe="")
    return build_tools_api_url(f"data/projects/{project_part}/cool")


def post_cool_project(
    *,
    project_slug: str,
    operation_id: str,
    timeout: int,
) -> requests.Response:
    url = _build_project_cool_url(project_slug)
    return requests.post(
        url,
        json={"operation_id": operation_id},
        timeout=timeout,
        headers=get_tools_api_auth_header(),
    )
