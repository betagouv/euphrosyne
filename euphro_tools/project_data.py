from __future__ import annotations

from urllib.parse import quote, urlencode

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


# pylint: disable=too-many-arguments
def post_delete_project_source_data(
    *,
    project_slug: str,
    storage_role: str,
    operation_id: str,
    file_count: int,
    total_size: int,
    timeout: int,
) -> requests.Response:
    project_part = quote(project_slug, safe="")
    storage_role_part = quote(storage_role, safe="")
    query_string = urlencode(
        {
            "operation_id": operation_id,
            "file_count": file_count,
            "total_size": total_size,
        }
    )
    url = build_tools_api_url(
        f"data/projects/{project_part}/delete/{storage_role_part}" f"?{query_string}"
    )
    return requests.post(
        url,
        timeout=timeout,
        headers=get_tools_api_auth_header(),
    )
