from collections.abc import Iterator
from unittest.mock import MagicMock, patch
from urllib.parse import unquote, urlsplit

import pytest
import requests
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from pytest import MonkeyPatch

from lab.runs.admin import RunAdmin
from lab.runs.models import Run
from lab.tests.factories import ProjectFactory, RunFactory

from ..hooks import (
    RenameFailedError,
    _make_request,
    initialize_project_directory,
    initialize_run_directory,
    rename_project_directory,
    rename_run_directory,
)


@pytest.fixture(name="http_mock")
def simulated_http(monkeypatch: MonkeyPatch) -> Iterator[MagicMock]:
    """Exercise real Requests preparation and redirects without network or real JWTs."""
    with (
        requests.Session() as session,
        patch("requests.adapters.HTTPAdapter.send") as send,
        patch("euphro_tools.hooks.EuphroToolsAPIToken.for_euphrosyne") as token,
    ):
        session.trust_env = False
        token.return_value.access_token = "test-service-token"
        monkeypatch.setattr(requests, "post", session.post)
        monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", "https://tools.example/api/")
        response = requests.Response()
        response.status_code = 204
        response._content = b""  # pylint: disable=protected-access
        send.return_value = response

        def respond(request: requests.PreparedRequest, **_kwargs) -> requests.Response:
            assert request.url is not None
            response.request = request
            response.url = request.url
            return response

        send.side_effect = respond
        yield send


@pytest.mark.parametrize(
    "name, encoded",
    [
        ("run-1_2", "run-1_2"),
        ("Run 1", "Run%201"),
        ("Échantillon 東京", "%C3%89chantillon%20%E6%9D%B1%E4%BA%AC"),
        ("run?mode=other#fragment", "run%3Fmode%3Dother%23fragment"),
        ("run..1", "run..1"),
        ("%2e%2e%2fadmin", "%252e%252e%252fadmin"),
        ("%2F%5c%3f%23", "%252F%255c%253f%2523"),
        ("%252e%252e%252fadmin", "%25252e%25252e%25252fadmin"),
    ],
)
@pytest.mark.parametrize(
    "operation, route",
    [
        (initialize_project_directory, "data/{name}/init"),
        (initialize_run_directory, "data/{name}/runs/{name}/init"),
        (rename_project_directory, "data/{name}/rename/{name}"),
        (rename_run_directory, "data/{name}/runs/{name}/rename/{name}"),
    ],
)
def test_directory_names_are_literal_segments(
    http_mock, name, encoded, operation, route
):
    operation(*[name] * route.count("{name}"))

    http_mock.assert_called_once()
    request = http_mock.call_args[0][0]
    assert request.method == "POST"
    assert request.url == f"https://tools.example/api/{route.format(name=encoded)}"
    parsed = urlsplit(request.url)
    assert parsed.netloc == "tools.example"
    assert parsed.query == parsed.fragment == ""
    assert unquote(parsed.path) == f"/api/{route.format(name=name)}"
    assert request.headers["Authorization"] == "Bearer test-service-token"
    assert http_mock.call_args.kwargs["timeout"] == 5


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../admin",
        "run/other",
        "run\\other",
        "//evil.example",
        "a\n",
        "a\x00",
        "a\x7f",
    ],
)
@pytest.mark.parametrize(
    "operation, arguments, position",
    [
        (initialize_project_directory, ["project"], 0),
        (initialize_run_directory, ["project", "run"], 0),
        (initialize_run_directory, ["project", "run"], 1),
        (rename_project_directory, ["project", "new-project"], 0),
        (rename_project_directory, ["project", "new-project"], 1),
        (rename_run_directory, ["project", "run", "new-run"], 0),
        (rename_run_directory, ["project", "run", "new-run"], 1),
        (rename_run_directory, ["project", "run", "new-run"], 2),
    ],
)
def test_invalid_segments_never_send_a_token(
    http_mock, name, operation, arguments, position
):
    arguments = arguments.copy()
    arguments[position] = name
    with pytest.raises(ValueError, match="directory path segment"):
        operation(*arguments)
    http_mock.assert_not_called()


@pytest.mark.parametrize(
    "base_url",
    [
        "//evil.example",
        "file:///tmp/tools",
        "https:///api",
        "https://user:password@tools.example",
        "https://tools.example?query",
        "https://tools.example#fragment",
        "https://tools.example\\evil",
        "https://tools.example/\napi",
    ],
)
def test_invalid_config_never_sends_a_token(http_mock, monkeypatch, base_url):
    monkeypatch.setenv("EUPHROSYNE_TOOLS_API_URL", base_url)
    with pytest.raises(ValueError, match="EUPHROSYNE_TOOLS_API_URL"):
        initialize_run_directory("project", "run")
    http_mock.assert_not_called()


@pytest.mark.parametrize("status_code", [301, 302, 303, 307, 308])
@pytest.mark.parametrize(
    "location",
    [
        "https://evil.example/collect-token",
        "//evil.example/collect-token",
        "http://169.254.169.254/latest/meta-data/",
        "https://tools.example/other-route",
        "/other-route",
    ],
)
@pytest.mark.parametrize("operation", [initialize_run_directory, rename_run_directory])
def test_run_redirects_are_refused_before_any_second_request(
    http_mock, caplog, status_code, location, operation
):
    http_mock.return_value.status_code = status_code
    http_mock.return_value.headers["Location"] = location
    arguments = ["project", "run"]
    if operation is rename_run_directory:
        arguments.append("new-run")
    operation(*arguments)

    http_mock.assert_called_once()
    request = http_mock.call_args[0][0]
    assert urlsplit(request.url).netloc == "tools.example"
    assert request.headers["Authorization"] == "Bearer test-service-token"
    assert "redirects are not allowed" in caplog.text
    assert "test-service-token" not in caplog.text
    assert location not in caplog.text


def test_make_request_can_raise_on_redirect(http_mock):
    http_mock.return_value.status_code = 307
    http_mock.return_value.headers["Location"] = "https://evil.example"
    with pytest.raises(requests.HTTPError, match="redirects are not allowed"):
        _make_request("https://tools.example/data/project/init", raise_on_error=True)
    http_mock.assert_called_once()


def test_project_rename_reports_redirect_failure(http_mock):
    http_mock.return_value.status_code = 308
    http_mock.return_value.headers["Location"] = "https://evil.example"
    with pytest.raises(RenameFailedError):
        rename_project_directory("project", "new-project")
    http_mock.assert_called_once()


@pytest.mark.parametrize("status_code", [400, 500])
def test_run_http_errors_keep_existing_failure_behavior(http_mock, caplog, status_code):
    http_mock.return_value.status_code = status_code
    initialize_run_directory("project", "run")
    assert "Could not init run" in caplog.text
    assert str(status_code) in caplog.text
    assert "test-service-token" not in caplog.text
    http_mock.assert_called_once()


@pytest.mark.django_db
@pytest.mark.parametrize("change", [False, True])
@pytest.mark.parametrize("name", ["Run 1", "Échantillon 東京"])
def test_admin_saves_names_and_calls_existing_tools_routes(http_mock, change, name):
    run = RunFactory(label="Original run") if change else Run(project=ProjectFactory())
    run.label = name
    run.full_clean()
    form = MagicMock(changed_data=["label"], initial={"label": "Original run"})
    RunAdmin(Run, admin_site=AdminSite()).save_model(
        RequestFactory().post("/admin/lab/run/"), run, form, change
    )

    run.refresh_from_db()
    assert run.label == name
    http_mock.assert_called_once()
    request = http_mock.call_args[0][0]
    suffix = f"Original run/rename/{name}" if change else f"{name}/init"
    assert unquote(urlsplit(request.url).path) == (
        f"/api/data/{run.project.slug}/runs/{suffix}"
    )
    assert request.headers["Authorization"] == "Bearer test-service-token"
