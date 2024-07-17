from typing import Literal


def get_run_data_path(
    project_slug: str, run_label: str, data_type: Literal["raw_data", "processed_data"]
):
    return _get_run_path(project_slug, run_label) + f"/{data_type}"


def _get_run_path(project_slug: str, run_label: str):
    return _get_project_path(project_slug) + f"/runs/{run_label}"


def _get_project_path(project_slug: str):
    return f"projects/{project_slug}"
