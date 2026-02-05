"""Compute project data totals (bytes + files) via tools-api listings."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal, TypedDict
from urllib.parse import quote

import requests

from .exceptions import EuphroToolsException
from .utils import build_tools_api_url, get_tools_api_auth_header


class ProjectDataListItem(TypedDict):
    name: str
    path: str
    last_modified: str | None
    size: int | None
    type: Literal["file", "directory"]


@dataclass(frozen=True)
class ProjectDataTotals:
    bytes_total: int
    files_total: int


def _build_project_data_url(project_slug: str) -> str:
    project_part = quote(project_slug, safe="")
    return build_tools_api_url(f"/data/{project_part}")


def _build_project_cool_url(project_slug: str) -> str:
    project_part = quote(project_slug, safe="")
    return build_tools_api_url(f"/data/projects/{project_part}/cool")


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


def _list_project_data_entries(
    project_slug: str,
    folder: str | None = None,
) -> list[ProjectDataListItem]:
    url = _build_project_data_url(project_slug)
    params = {"folder": folder} if folder else None
    response = requests.get(
        url,
        params=params,
        timeout=5,
        headers=get_tools_api_auth_header(),
    )
    if response.status_code == 404:
        raise EuphroToolsException("Project data not found for %s." % project_slug)
    if not response.ok:
        raise EuphroToolsException(
            "Failed to list project data entries for %s." % project_slug
        )
    payload = response.json()
    if not isinstance(payload, list):
        raise EuphroToolsException(
            "Unexpected project data listing response for %s." % project_slug
        )
    return payload


def _join_folder(parent: str | None, name: str) -> str:
    if parent:
        return f"{parent}/{name}"
    return name


def compute_project_data_totals(project_slug: str) -> ProjectDataTotals:
    bytes_total = 0
    files_total = 0
    pending_folders: deque[str | None] = deque([None])
    while pending_folders:
        folder = pending_folders.popleft()
        for entry in _list_project_data_entries(project_slug, folder=folder):
            if entry.get("type") == "directory":
                pending_folders.append(_join_folder(folder, entry["name"]))
                continue
            size = entry.get("size")
            if size is None:
                raise EuphroToolsException(
                    "Missing size for project data entry %s."
                    % (entry.get("path", entry.get("name", "unknown")),)
                )
            bytes_total += int(size)
            files_total += 1
    return ProjectDataTotals(bytes_total=bytes_total, files_total=files_total)
