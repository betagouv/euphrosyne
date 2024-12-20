import datetime
from unittest import mock

from django.test import TestCase

from ..data_links import NUM_DAYS_VALID, send_links
from . import factories


class DataLinksTestCase(TestCase):
    def setUp(self):
        patcher = mock.patch(
            "data_request.data_links.fetch_token_for_run_data", return_value="token"
        )
        self.fetch_token_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            "data_request.data_links.generate_download_url", return_value="http://url"
        )
        self.generate_download_url_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch("data_request.data_links.send_data_email")
        self.send_data_email_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_send_links_set_expiration(self):
        dr = factories.DataRequestWithRunsFactory()
        now = datetime.datetime.now()
        expiration = now + datetime.timedelta(days=NUM_DAYS_VALID)

        with mock.patch("data_request.data_links.datetime.datetime") as datetime_mock:
            datetime_mock.now.return_value = now
            send_links(dr)
            # data_type raw_data
            assert (
                self.fetch_token_mock.call_args_list[0][1]["expiration"] == expiration
            )

    def test_send_data_email_context(self):
        dr = factories.DataRequestFactory()
        dr.runs.add(
            factories.RunFactory(project__name="Project 1", label="Run 1"),
        )

        send_links(dr)

        # data_type raw_data
        assert self.send_data_email_mock.call_args_list[0][1]["context"]["links"] == [
            {"name": "Run 1 (Project 1)", "url": "http://url", "data_type": "raw_data"},
        ]
        self.generate_download_url_mock.assert_has_calls(
            [
                mock.call(
                    data_type="raw_data",
                    project_slug="project-1",
                    run_label="Run 1",
                    token="token",
                ),
            ],
            any_order=True,
        )

    def test_send_data_email_context_when_multiple_runs(self):
        dr = factories.DataRequestWithRunsFactory()

        send_links(dr)

        assert (
            len(self.send_data_email_mock.call_args_list[0][1]["context"]["links"]) == 3
        )
