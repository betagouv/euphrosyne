from unittest import mock

from django.core.management import call_command
from django.test import TestCase


class TestRunChecksCommand(TestCase):
    @mock.patch("lab.management.commands.run_checks.apps.is_installed")
    @mock.patch("lab.management.commands.run_checks.management.call_command")
    def test_calls_employer_information_reminders_when_radiation_protection_enabled(
        self, mock_call_command, mock_is_installed
    ):
        mock_is_installed.side_effect = (
            lambda app_name: app_name == "radiation_protection"
        )

        call_command("run_checks")

        mock_call_command.assert_any_call("send_employer_information_reminders")

    @mock.patch("lab.management.commands.run_checks.apps.is_installed")
    @mock.patch("lab.management.commands.run_checks.management.call_command")
    def test_does_not_call_employer_information_reminders_when_disabled(
        self, mock_call_command, mock_is_installed
    ):
        mock_is_installed.return_value = False

        call_command("run_checks")

        assert mock.call("send_employer_information_reminders") not in (
            mock_call_command.call_args_list
        )
