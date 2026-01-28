"""Compute run data totals (bytes + files) via tools-api listings."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal, TypedDict
from urllib.parse import quote

import requests

from .exceptions import EuphroToolsException
from .utils import build_tools_api_url, get_tools_api_auth_header


class RunDataListItem(TypedDict):
    name: str
    path: str
    last_modified: str | None
    size: int | None
    type: Literal["file", "directory"]


@dataclass(frozen=True)
class RunDataTotals:
    bytes_total: int
    files_total: int


def _build_run_data_url(project_slug: str, run_label: str) -> str:
    project_part = quote(project_slug, safe="")
    run_part = quote(run_label, safe="")
    return build_tools_api_url(f"/data/{project_part}/runs/{run_part}")


def _list_run_data_entries(
    project_slug: str,
    run_label: str,
    folder: str | None = None,
) -> list[RunDataListItem]:
    url = _build_run_data_url(project_slug, run_label)
    params = {"folder": folder} if folder else None
    response = requests.get(
        url,
        params=params,
        timeout=5,
        headers=get_tools_api_auth_header(),
    )
    if response.status_code == 404:
        raise EuphroToolsException(
            "Run data not found for %s/%s." % (project_slug, run_label)
        )
    if not response.ok:
        raise EuphroToolsException(
            "Failed to list run data entries for %s/%s." % (project_slug, run_label)
        )
    payload = response.json()
    if not isinstance(payload, list):
        raise EuphroToolsException(
            "Unexpected run data listing response for %s/%s."
            % (project_slug, run_label)
        )
    return payload


def _join_folder(parent: str | None, name: str) -> str:
    if parent:
        return f"{parent}/{name}"
    return name


def compute_run_data_totals(
    project_slug: str,
    run_label: str,
) -> RunDataTotals:
    bytes_total = 0
    files_total = 0
    pending_folders: deque[str | None] = deque([None])
    while pending_folders:
        folder = pending_folders.popleft()
        for entry in _list_run_data_entries(project_slug, run_label, folder=folder):
            if entry.get("type") == "directory":
                pending_folders.append(_join_folder(folder, entry["name"]))
                continue
            size = entry.get("size")
            if size is None:
                raise EuphroToolsException(
                    "Missing size for run data entry %s."
                    % (entry.get("path", entry.get("name", "unknown")),)
                )
            bytes_total += int(size)
            files_total += 1
    return RunDataTotals(bytes_total=bytes_total, files_total=files_total)
