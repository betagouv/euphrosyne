from unittest.mock import MagicMock, patch

import requests
from pytest import MonkeyPatch

from ..hooks import (
    _make_request,
    initialize_project_directory,
    initialize_run_directory,
    rename_project_directory,
    rename_run_directory,
)


@patch("euphro_tools.hooks.requests")
def test_initialize_project_directory(
    requests_mock: MagicMock, monkeypatch: MonkeyPatch
):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "http://euphro.tools")
    initialize_project_directory("project")

    requests_mock.post.assert_called_once()
    assert requests_mock.post.call_args[0] == ("http://euphro.tools/data/project/init",)


@patch("euphro_tools.hooks.requests")
def test_initialize_run_directory(requests_mock: MagicMock, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "http://euphro.tools")
    initialize_run_directory("project", "run")

    requests_mock.post.assert_called_once()
    assert requests_mock.post.call_args[0] == (
        "http://euphro.tools/data/project/runs/run/init",
    )


@patch("euphro_tools.hooks.requests")
def test_rename_run_directory(requests_mock: MagicMock, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "http://euphro.tools")
    rename_run_directory("project", "run", "newname")

    requests_mock.post.assert_called_once()
    assert requests_mock.post.call_args[0] == (
        "http://euphro.tools/data/project/runs/run/rename/newname",
    )


@patch("euphro_tools.hooks.requests")
def test_rename_project_directory(requests_mock: MagicMock, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "http://euphro.tools")
    rename_project_directory("project", "newname")

    requests_mock.post.assert_called_once()
    assert requests_mock.post.call_args[0] == (
        "http://euphro.tools/data/project/rename/newname",
    )


@patch("euphro_tools.hooks.requests")
@patch("euphro_tools.hooks.EuphroToolsAPIToken")
def test_make_request_has_auth_header(
    token_class_mock: MagicMock, request_mock: MagicMock
):
    _make_request("https://url")
    token_class_mock.for_euphrosyne.assert_called()
    assert "Authorization" in request_mock.post.call_args[1]["headers"]
    assert request_mock.post.call_args[1]["headers"]["Authorization"].startswith(
        "Bearer "
    )


@patch("euphro_tools.hooks.logger")
@patch("euphro_tools.hooks.requests.post")
def test_make_request_log_error_on_timeout(
    request_post_mock: MagicMock, logger_mock: MagicMock
):
    request_post_mock.side_effect = requests.Timeout()
    _make_request("https://url")

    logger_mock.error.assert_called()
