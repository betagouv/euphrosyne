from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from lab.management.commands.alert_end_run_embargos import (
    get_runs_with_embargos_ending_in_range,
)

from ... import factories


class TestEmbargosEndingInRangeFromNowTest(TestCase):
    def setUp(self):
        self.run1 = factories.RunFactory(
            embargo_date=timezone.now() + timedelta(days=32)
        )
        self.run2 = factories.RunFactory(
            embargo_date=timezone.now() + timedelta(days=35)
        )
        self.run3 = factories.RunFactory(
            embargo_date=timezone.now() + timedelta(days=40)
        )

    def test_embargos_ending_in_range(self):
        runs = get_runs_with_embargos_ending_in_range(30, 36)
        self.assertIn(self.run1, runs)
        self.assertIn(self.run2, runs)
        self.assertNotIn(self.run3, runs)

    def test_no_embargos_ending_in_range(self):
        runs = get_runs_with_embargos_ending_in_range(37, 40)
        self.assertNotIn(self.run1, runs)
        self.assertNotIn(self.run2, runs)
        self.assertIn(self.run3, runs)


class TestAlertEndRunEmbargosCommand(TestCase):

    @mock.patch(
        "lab.management.commands.alert_end_run_embargos.send_ending_embargo_email"
    )
    def test_send_ending_embargo_email_called(
        self, mock_send_ending_embargo_email: mock.MagicMock
    ):
        with mock.patch(
            "lab.management.commands.alert_end_run_embargos.timezone"
        ) as mock_timezone:
            # Saturday, 2025-02-01
            mock_timezone.now.return_value = datetime(
                2025, 2, 1, 14, 10, 26, tzinfo=dt_timezone.utc
            )

            factories.RunFactory(
                embargo_date=datetime(2025, 3, 2, 10, 00, 00, tzinfo=dt_timezone.utc),
                project=factories.ProjectWithLeaderFactory(),
            )  # not in range
            run2 = factories.RunFactory(
                embargo_date=datetime(2025, 3, 3, 10, 00, 00, tzinfo=dt_timezone.utc),
                project=factories.ProjectWithLeaderFactory(),
            )  # in range
            run3 = factories.RunFactory(
                embargo_date=datetime(2025, 3, 9, 10, 00, 00, tzinfo=dt_timezone.utc),
                project=factories.ProjectWithLeaderFactory(),
            )  # in range
            factories.RunFactory(
                embargo_date=datetime(2025, 3, 10, 10, 00, 00, tzinfo=dt_timezone.utc),
                project=factories.ProjectWithLeaderFactory(),
            )  # not in range
            call_command("alert_end_run_embargos")

        assert len(mock_send_ending_embargo_email.call_args_list) == 2
        assert mock_send_ending_embargo_email.call_args_list[0][1]["emails"] == [
            run2.project.leader.user.email
        ]
        assert mock_send_ending_embargo_email.call_args_list[0][1]["run"] == run2
        assert mock_send_ending_embargo_email.call_args_list[1][1]["emails"] == [
            run3.project.leader.user.email
        ]
        assert mock_send_ending_embargo_email.call_args_list[1][1]["run"] == run3
