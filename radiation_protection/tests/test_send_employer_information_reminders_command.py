from datetime import date, datetime
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from lab.tests import factories as lab_factories


class TestSendEmployerInformationRemindersCommand(TestCase):
    def _call_command(self, today):
        with (
            mock.patch(
                "radiation_protection.management.commands.send_employer_information_reminders.app_settings.RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS",  # pylint: disable=line-too-long
                ["admin@example.com"],
            ),
            mock.patch(
                "radiation_protection.management.commands.send_employer_information_reminders.send_employer_information_reminder",  # pylint: disable=line-too-long
                return_value=True,
            ) as mock_send_participant,
            mock.patch(
                "radiation_protection.management.commands.send_employer_information_reminders.send_employer_information_reminder_summary",  # pylint: disable=line-too-long
                return_value=True,
            ) as mock_send_summary,
            mock.patch(
                "radiation_protection.management.commands.send_employer_information_reminders.timezone.localdate",  # pylint: disable=line-too-long
                return_value=today,
            ),
        ):
            call_command("send_employer_information_reminders")
        return mock_send_participant, mock_send_summary

    def test_sends_reminders_for_runs_starting_in_seven_days(self):
        today = date(2026, 5, 6)
        seven_day_run = lab_factories.RunFactory(
            start_date=timezone.make_aware(
                datetime.combine(date(2026, 5, 13), datetime.min.time())
            )
        )
        lab_factories.RunFactory(
            start_date=timezone.make_aware(
                datetime.combine(date(2026, 5, 15), datetime.min.time())
            )
        )
        seven_day_participation = lab_factories.ParticipationFactory(
            project=seven_day_run.project,
            on_premises=True,
            employer=None,
            institution=lab_factories.InstitutionFactory(ror_id="https://ror.org/non"),
        )

        mock_send_participant, mock_send_summary = self._call_command(today)

        mock_send_participant.assert_called_once_with(
            seven_day_participation, seven_day_run
        )
        mock_send_summary.assert_called_once_with(
            ["admin@example.com"], seven_day_run, [seven_day_participation]
        )

    def test_sends_reminders_for_runs_starting_in_two_days(self):
        today = date(2026, 5, 6)
        two_day_run = lab_factories.RunFactory(
            start_date=timezone.make_aware(
                datetime.combine(date(2026, 5, 8), datetime.min.time())
            )
        )
        lab_factories.RunFactory(
            start_date=timezone.make_aware(
                datetime.combine(date(2026, 5, 9), datetime.min.time())
            )
        )
        two_day_participation = lab_factories.ParticipationFactory(
            project=two_day_run.project,
            on_premises=True,
            employer=None,
            institution=lab_factories.InstitutionFactory(ror_id="https://ror.org/non"),
        )

        mock_send_participant, mock_send_summary = self._call_command(today)

        mock_send_participant.assert_called_once_with(
            two_day_participation, two_day_run
        )
        mock_send_summary.assert_called_once_with(
            ["admin@example.com"], two_day_run, [two_day_participation]
        )

    @override_settings(
        PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS=["https://ror.org/exempt"]
    )
    def test_excludes_complete_remote_and_employer_form_exempt_participations(self):
        today = date(2026, 5, 6)
        run = lab_factories.RunFactory(
            start_date=timezone.make_aware(
                datetime.combine(date(2026, 5, 13), datetime.min.time())
            )
        )
        incomplete_participation = lab_factories.ParticipationFactory(
            project=run.project,
            on_premises=True,
            employer=None,
            institution=lab_factories.InstitutionFactory(ror_id="https://ror.org/non"),
        )
        lab_factories.ParticipationFactory(
            project=run.project,
            on_premises=True,
            employer=lab_factories.EmployerFactory(),
            institution=lab_factories.InstitutionFactory(ror_id="https://ror.org/non"),
        )
        lab_factories.ParticipationFactory(
            project=run.project,
            on_premises=False,
            employer=None,
        )
        lab_factories.ParticipationFactory(
            project=run.project,
            on_premises=True,
            employer=None,
            institution=lab_factories.InstitutionFactory(
                ror_id="https://ror.org/exempt"
            ),
        )

        mock_send_participant, mock_send_summary = self._call_command(today)

        mock_send_participant.assert_called_once_with(incomplete_participation, run)
        mock_send_summary.assert_called_once_with(
            ["admin@example.com"], run, [incomplete_participation]
        )
