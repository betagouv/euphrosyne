import os
from typing import Literal


def _get_euphrosyne_token():
    from euphro_auth.jwt.tokens import (  # pylint: disable=import-outside-toplevel
        EuphroToolsAPIToken,
    )

    return EuphroToolsAPIToken.for_euphrosyne().access_token


def get_run_data_path(
    project_slug: str, run_label: str, data_type: Literal["raw_data", "processed_data"]
):
    return _get_run_path(project_slug, run_label) + f"/{data_type}"


def build_tools_api_url(path: str) -> str:
    base_url = os.environ.get("EUPHROSYNE_TOOLS_API_URL")
    if base_url is None:
        raise RuntimeError(
            "Environment variable 'EUPHROSYNE_TOOLS_API_URL' is not set. "
            "Please configure it to point to the Euphrosyne Tools API base URL."
        )
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"


def get_tools_api_auth_header() -> dict[str, str]:
    token = _get_euphrosyne_token()
    return {"Authorization": f"Bearer {token}"}


def _get_run_path(project_slug: str, run_label: str):
    return _get_project_path(project_slug) + f"/runs/{run_label}"


def _get_project_path(project_slug: str):
    return f"projects/{project_slug}"
