import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from ...factories import ProjectFactory


class CheckLongRunningVMsTest(TestCase):
    @patch("requests.get")
    @patch("euphro_auth.jwt.tokens.EuphroToolsAPIToken.for_euphrosyne")
    def test_no_long_running_vms(self, mock_token, mock_get):
        mock_token.return_value.access_token = "fake_token"
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = []

        with patch("django.utils.timezone.now", return_value=timezone.now()):
            call_command("check_long_running_vms", "60")

        mock_get.assert_called_once_with(
            os.environ["EUPHROSYNE_TOOLS_API_URL"]
            + "/vms?created_before="
            + (timezone.now() - timedelta(minutes=60)).isoformat(timespec="seconds"),
            timeout=5,
            headers={"Authorization": "Bearer fake_token"},
        )

    @patch("requests.get")
    @patch("euphro_auth.jwt.tokens.EuphroToolsAPIToken.for_euphrosyne")
    def test_long_running_vms_found(self, mock_token, mock_get):
        mock_token.return_value.access_token = "fake_token"
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = ["project1-vm-123"]

        with patch("django.utils.timezone.now", return_value=timezone.now()):
            call_command("check_long_running_vms", "60")

        mock_get.assert_called_once_with(
            os.environ["EUPHROSYNE_TOOLS_API_URL"]
            + "/vms?created_before="
            + (timezone.now() - timedelta(minutes=60)).isoformat(timespec="seconds"),
            timeout=5,
            headers={"Authorization": "Bearer fake_token"},
        )

    @patch("requests.get")
    @patch("euphro_auth.jwt.tokens.EuphroToolsAPIToken.for_euphrosyne")
    @patch("lab.management.commands.check_long_running_vms.send_long_lasting_email")
    def test_send_alerts(self, mock_send_email, mock_token, mock_get):
        project = ProjectFactory()
        mock_token.return_value.access_token = "fake_token"
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = [f"euphrosyne-prod-vm-{project.slug}"]

        group = Group.objects.get(name="vm admin")
        group.user_set.create(email="admin@example.com")

        now = timezone.now()

        with patch("django.utils.timezone.now", return_value=now):
            call_command("check_long_running_vms", "60", "--send-alerts")

        mock_get.assert_called_once_with(
            os.environ["EUPHROSYNE_TOOLS_API_URL"]
            + "/vms?created_before="
            + (now - timedelta(minutes=60)).isoformat(timespec="seconds"),
            timeout=5,
            headers={"Authorization": "Bearer fake_token"},
        )
        mock_send_email.assert_called_once_with(["admin@example.com"], project)
