from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.management import call_command

from data_management.models import RunData
from euphro_tools.run_data import RunDataTotals, compute_run_data_totals
from lab.runs.models import Run
from lab.tests.factories import RunFactory


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


@pytest.mark.django_db
def test_compute_run_data_totals_command_updates_run_data():
    run = RunFactory(status=Run.Status.FINISHED)
    run_data = RunData.objects.create(run=run)

    with patch(
        "data_management.management.commands.compute_run_data_totals.compute_run_data_totals"  # pylint: disable=line-too-long
    ) as mock_compute:
        mock_compute.return_value = RunDataTotals(bytes_total=10, files_total=2)
        call_command("compute_run_data_totals")

    run_data.refresh_from_db()
    assert run_data.run_size_bytes == 10
    assert run_data.file_count == 2
    mock_compute.assert_called_once_with(run.project.slug, run.label)
