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

        patcher = mock.patch(
            "euphro_tools.download_urls.EuphroRefreshToken.for_euphrosyne_admin_user"
        )
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

        self.token_mock.return_value.access_token = "access"

    def test_generate_download_url(self):
        url = generate_download_url("project_slug", "run_label", "raw_data", "token")
        assert (
            url
            # pylint: disable=line-too-long
            == "http://example.com/data/run-data-zip?token=token&path=projects/project_slug/runs/run_label/raw_data"
        )

    def test_fetch_token_for_run_data(self):
        now = datetime.now()
        self.requests_get_mock.return_value.json.return_value = {"token": "token"}

        token = fetch_token_for_run_data(
            "project_slug", "run_label", "raw_data", expiration=now
        )

        assert token == "token"
        assert self.requests_get_mock.call_args[0][0] == (
            # pylint: disable=line-too-long
            "http://example.com/data/project_slug/token?path=projects/project_slug/runs/run_label/raw_data"
        )
        assert self.requests_get_mock.call_args[1]["headers"] == {
            "Authorization": "Bearer access"
        }

    def test_fetch_token_for_run_data_raise_euphro_tools_exception(
        self,
    ):
        self.requests_get_mock.side_effect = HTTPError()

        with pytest.raises(EuphroToolsException):
            fetch_token_for_run_data("project_slug", "run_label", "raw_data")
