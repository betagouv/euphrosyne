from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import requests

from euphro_tools.exceptions import EuphroToolsException
from euphro_tools.run_data import compute_run_data_totals


def build_response(payload, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.ok = status_code == 200
    response.status_code = status_code
    response.json.return_value = payload
    return response


def test_compute_run_data_totals_counts_files_and_bytes(monkeypatch):
    monkeypatch.setattr(
        "euphro_auth.jwt.tokens.EuphroToolsAPIToken.for_euphrosyne",
        lambda: SimpleNamespace(access_token="token"),
    )

    get_mock = MagicMock(
        side_effect=[
            build_response(
                [
                    {
                        "name": "file1.txt",
                        "path": "path/file1.txt",
                        "last_modified": "2024-01-01",
                        "size": 5,
                        "type": "file",
                    },
                    {
                        "name": "dir1",
                        "path": "path/dir1",
                        "last_modified": "2024-01-01",
                        "size": 0,
                        "type": "directory",
                    },
                ]
            ),
            build_response(
                [
                    {
                        "name": "file2.txt",
                        "path": "path/dir1/file2.txt",
                        "last_modified": "2024-01-01",
                        "size": 7,
                        "type": "file",
                    }
                ]
            ),
        ]
    )
    monkeypatch.setattr(requests, "get", get_mock)

    totals = compute_run_data_totals("project-slug", "run label")

    assert totals.bytes_total == 12
    assert totals.files_total == 2


def test_compute_run_data_totals_raises_on_missing_run(monkeypatch):
    monkeypatch.setattr(
        "euphro_auth.jwt.tokens.EuphroToolsAPIToken.for_euphrosyne",
        lambda: SimpleNamespace(access_token="token"),
    )

    get_mock = MagicMock(
        return_value=build_response([], status_code=404),
    )
    monkeypatch.setattr(requests, "get", get_mock)

    with pytest.raises(EuphroToolsException):
        compute_run_data_totals("project-slug", "missing-run")
