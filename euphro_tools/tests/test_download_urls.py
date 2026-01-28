from datetime import datetime
from unittest import mock

import pytest
from django.test import TestCase
from requests.exceptions import HTTPError

from euphro_tools.exceptions import EuphroToolsException

from ..download_urls import fetch_token_for_run_data, generate_download_url


class TestDownloaldUrls(TestCase):
    def setUp(self):
        patcher = mock.patch("euphro_tools.download_urls.requests.get")
        self.requests_get_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch("euphro_tools.utils._get_euphrosyne_token")
        self.token_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch.dict(
            "os.environ",
            {
                "EUPHROSYNE_TOOLS_API_URL": "http://example.com",
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.token_mock.return_value = "access"

    def test_generate_download_url(self):
        url = generate_download_url("project_slug", "run_label", "raw_data", "token")
        assert (
            url
            # pylint: disable=line-too-long
            == "http://example.com/data/run-data-zip?token=token&path=projects%2Fproject_slug%2Fruns%2Frun_label%2Fraw_data"
        )

    def test_fetch_token_for_run_data(self):
        now = datetime.now()
        self.requests_get_mock.return_value.json.return_value = {"token": "token"}

        token = fetch_token_for_run_data(
            "project_slug", "run_label", "raw_data", expiration=now
        )

        assert token == "token"
        url = self.requests_get_mock.call_args[0][0]
        assert url == "http://example.com/data/project_slug/token"
        params = self.requests_get_mock.call_args[1]["params"]
        assert params == {
            "path": "projects/project_slug/runs/run_label/raw_data",
            "expiration": now.isoformat(),
        }
        assert self.requests_get_mock.call_args[1]["headers"] == {
            "Authorization": "Bearer access"
        }

    def test_fetch_token_for_run_data_with_data_request_id(self):
        self.requests_get_mock.return_value.json.return_value = {"token": "token"}
        fetch_token_for_run_data(
            "project_slug", "run_label", "raw_data", data_request_id="1"
        )
        params = self.requests_get_mock.call_args[1]["params"]
        assert params["data_request"] == "1"

    def test_fetch_token_for_run_data_raise_euphro_tools_exception(
        self,
    ):
        self.requests_get_mock.side_effect = HTTPError()

        with pytest.raises(EuphroToolsException):
            fetch_token_for_run_data("project_slug", "run_label", "raw_data")
