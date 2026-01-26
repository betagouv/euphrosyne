import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from ...factories import ProjectFactory


class CheckLongRunningVMsTest(TestCase):
    def setUp(self):
        self.token_patcher = patch(
            "euphro_auth.jwt.tokens.EuphroToolsAPIToken.for_euphrosyne"
        )
        self.mock_token = self.token_patcher.start()
        self.mock_token.return_value.access_token = "fake_token"

        self.get_patcher = patch("requests.get")
        self.mock_get = self.get_patcher.start()
        self.mock_get.return_value.ok = True

        self.now = datetime.now(timezone.utc)
        self.datetime_mock = MagicMock(now=MagicMock(return_value=self.now))
        self.datetime_patcher = patch(
            "lab.management.commands.check_long_running_vms.datetime",
            self.datetime_mock,
        )
        self.datetime_patcher.start()

    def tearDown(self):
        self.token_patcher.stop()
        self.get_patcher.stop()
        self.datetime_patcher.stop()

    def _get_expected_api_call(self, minutes: int):
        expected_time = (self.now - timedelta(minutes=minutes)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return (
            os.environ["EUPHROSYNE_TOOLS_API_URL"]
            + "/vms?created_before="
            + expected_time
        )

    # TESTS #

    def test_no_long_running_vms(self):
        self.mock_get.return_value.json.return_value = []

        call_command("check_long_running_vms", "60")

        self.mock_get.assert_called_once_with(
            self._get_expected_api_call(60),
            timeout=10,
            headers={"Authorization": "Bearer fake_token"},
        )

    def test_long_running_vms_found(self):
        self.mock_get.return_value.json.return_value = ["project1-vm-123"]

        call_command("check_long_running_vms", "60")

        self.mock_get.assert_called_once_with(
            self._get_expected_api_call(60),
            timeout=10,
            headers={"Authorization": "Bearer fake_token"},
        )

    @patch("lab.management.commands.check_long_running_vms.send_long_lasting_email")
    def test_send_alerts(self, mock_send_email):
        project = ProjectFactory()
        self.mock_get.return_value.json.return_value = [
            f"euphrosyne-prod-vm-{project.slug}"
        ]

        group = Group.objects.get(name="vm admin")
        group.user_set.create(email="admin@example.com")

        call_command("check_long_running_vms", "60", "--send-alerts")

        self.mock_get.assert_called_once_with(
            self._get_expected_api_call(60),
            timeout=10,
            headers={"Authorization": "Bearer fake_token"},
        )
        mock_send_email.assert_called_once_with(["admin@example.com"], project)
