import datetime
from unittest import mock

from django.test import TestCase

from lab.management.commands.finish_runs import Command
from lab.models import Run

from ...factories import RunFactory


class FinishRunCommandTestCase(TestCase):
    @mock.patch("lab.management.commands.finish_runs.timezone")
    def test_finish_run_command(self, timezone_patch: mock.MagicMock):
        timezone_patch.now.return_value = datetime.datetime(2023, 2, 23)

        og_this_week_run = RunFactory(
            end_date=datetime.datetime(2023, 2, 21), status=Run.Status.ONGOING
        )
        og_last_week_run = RunFactory(
            end_date=datetime.datetime(2023, 2, 17), status=Run.Status.ONGOING
        )
        cr_2w_run = RunFactory(
            end_date=datetime.datetime(2023, 2, 8), status=Run.Status.CREATED
        )

        Command().handle()

        og_this_week_run.refresh_from_db()
        og_last_week_run.refresh_from_db()
        cr_2w_run.refresh_from_db()

        self.assertTrue(og_this_week_run.status == Run.Status.ONGOING)  # no change
        self.assertTrue(og_last_week_run.status == Run.Status.FINISHED)  # change
        self.assertTrue(cr_2w_run.status == Run.Status.FINISHED)  # change
