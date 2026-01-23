import os
from typing import Literal

from euphro_auth.jwt.tokens import EuphroToolsAPIToken


def get_run_data_path(
    project_slug: str, run_label: str, data_type: Literal["raw_data", "processed_data"]
):
    return _get_run_path(project_slug, run_label) + f"/{data_type}"


def build_tools_api_url(path: str) -> str:
    base_url = os.environ["EUPHROSYNE_TOOLS_API_URL"]
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"


def get_tools_api_auth_header() -> dict[str, str]:
    token = EuphroToolsAPIToken.for_euphrosyne().access_token
    return {"Authorization": f"Bearer {token}"}


def _get_run_path(project_slug: str, run_label: str):
    return _get_project_path(project_slug) + f"/runs/{run_label}"


def _get_project_path(project_slug: str):
    return f"projects/{project_slug}"
