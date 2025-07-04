from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from euphro_auth.tests import factories as auth_factories
from lab.tests import factories as lab_factories
from radiation_protection.models import RiskPreventionPlan


class TestSendRiskPreventionPlansCommand(  # pylint: disable=too-many-public-methods
    TestCase
):
    """Test cases for send_risk_prevention_plans management command."""

    def setUp(self):
        """Set up test data for each test."""
        self.user = auth_factories.StaffUserFactory()
        self.project = lab_factories.ProjectFactory()
        self.participation = lab_factories.ParticipationFactory(
            user=self.user, project=self.project, on_premises=True
        )
        self.run = lab_factories.RunFactory(project=self.project)

        # Create a plan that needs to be processed
        self.plan = RiskPreventionPlan.objects.create(
            participation=self.participation,
            run=self.run,
            risk_advisor_notification_sent=False,
        )

    def _call_command(self):
        """Helper method to call the management command and capture output."""
        out = StringIO()
        err = StringIO()
        call_command("send_risk_prevention_plans", stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    # 1. Basic Functionality Tests

    def test_no_plans_to_process(self):
        """Test command when no plans need processing."""
        # Mark all plans as already sent
        RiskPreventionPlan.objects.all().update(risk_advisor_notification_sent=True)

        out, err = self._call_command()

        self.assertIn("Found 0 risk prevention plans to process", out)
        self.assertEqual(err, "")

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_single_plan_success_flow(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test successful processing of a single plan."""
        # Setup mocks
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = True

        out, err = self._call_command()

        # Verify plan was marked as sent
        self.plan.refresh_from_db()
        self.assertTrue(self.plan.risk_advisor_notification_sent)

        # Verify mock calls
        mock_fill_docs.assert_called_once_with(user=self.user, next_user_run=self.run)
        mock_send_docs.assert_called_once_with(
            self.plan, [("document.pdf", b"pdf_content")]
        )

        # Verify sentry extras were set
        mock_sentry.set_extra.assert_any_call("user", self.user.email)
        mock_sentry.set_extra.assert_any_call("run", self.run.id)

        # Verify output
        self.assertIn("Found 1 risk prevention plans to process", out)
        self.assertIn(
            f"Successfully generated and sent radiation protection document for user {self.user.email}",  # pylint: disable=line-too-long
            out,
        )
        self.assertEqual(err, "")

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_multiple_plans_all_succeed(self, _, mock_fill_docs, mock_send_docs):
        """Test successful processing of multiple plans."""
        # Create additional plans
        user2 = auth_factories.StaffUserFactory()
        participation2 = lab_factories.ParticipationFactory(
            user=user2, project=self.project, on_premises=True
        )
        plan2 = RiskPreventionPlan.objects.create(
            participation=participation2,
            run=self.run,
            risk_advisor_notification_sent=False,
        )

        # Setup mocks
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = True

        out, _ = self._call_command()

        # Verify both plans were marked as sent
        self.plan.refresh_from_db()
        plan2.refresh_from_db()
        self.assertTrue(self.plan.risk_advisor_notification_sent)
        self.assertTrue(plan2.risk_advisor_notification_sent)

        # Verify output
        self.assertIn("Found 2 risk prevention plans to process", out)
        self.assertEqual(mock_fill_docs.call_count, 2)
        self.assertEqual(mock_send_docs.call_count, 2)

    # 2. Document Generation Error Tests

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_document_generation_returns_none(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test handling when document generation returns None."""
        mock_fill_docs.return_value = None

        _, err = self._call_command()

        # Verify plan was not marked as sent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

        # Verify error handling
        mock_send_docs.assert_not_called()
        mock_sentry.capture_message.assert_called_once_with(
            "Failed to generate radiation protection document", level="error"
        )

        # Verify error output
        self.assertIn(
            f"Failed to generate radiation protection document for user {self.user.id}",
            err,
        )

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_document_generation_returns_empty_list(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test handling when document generation returns empty list."""
        mock_fill_docs.return_value = []

        self._call_command()

        # Verify plan was not marked as sent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

        # Verify error handling
        mock_send_docs.assert_not_called()
        mock_sentry.capture_message.assert_called_once()

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_document_generation_contains_none_values(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test handling when document generation returns list with None values."""
        mock_fill_docs.return_value = [None, ("file.pdf", b"data")]

        self._call_command()

        # Verify plan was not marked as sent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

        # Verify error handling
        mock_send_docs.assert_not_called()
        mock_sentry.capture_message.assert_called_once()

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_document_generation_all_none_values(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test handling when document generation returns all None values."""
        mock_fill_docs.return_value = [None, None]

        self._call_command()

        # Verify plan was not marked as sent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

        # Verify error handling
        mock_send_docs.assert_not_called()
        mock_sentry.capture_message.assert_called_once()

    # 3. Document Sending Error Tests

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_document_sending_fails(self, mock_sentry, mock_fill_docs, mock_send_docs):
        """Test handling when document sending fails."""
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = False

        _, err = self._call_command()

        # Verify plan was not marked as sent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

        # Verify error handling
        mock_sentry.capture_message.assert_called_once_with(
            "Failed to send radiation protection document to risk advisor",
            level="error",
        )

        # Verify error output
        self.assertIn(
            f"Failed to send radiation protection document to risk advisor for user {self.user.email}",  # pylint: disable=line-too-long
            err,
        )

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    def test_document_sending_fails_with_multiple_plans(
        self, mock_fill_docs, mock_send_docs
    ):
        """Test that command stops when document sending fails with multiple plans."""
        # Create additional plan
        user2 = auth_factories.StaffUserFactory()
        participation2 = lab_factories.ParticipationFactory(
            user=user2, project=self.project, on_premises=True
        )
        plan2 = RiskPreventionPlan.objects.create(
            participation=participation2,
            run=self.run,
            risk_advisor_notification_sent=False,
        )

        # Setup mocks - first succeeds, second fails
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.side_effect = [True, False]  # First call succeeds, second fails

        _, err = self._call_command()

        # Verify first plan was marked as sent, second was not
        self.plan.refresh_from_db()
        plan2.refresh_from_db()

        # The order depends on database ordering, so check that exactly one was sent
        sent_count = sum(
            [
                self.plan.risk_advisor_notification_sent,
                plan2.risk_advisor_notification_sent,
            ]
        )
        self.assertEqual(sent_count, 1, "Exactly one plan should be marked as sent")

        # Verify command stopped after failure
        self.assertIn(
            "Failed to send radiation protection document to risk advisor", err
        )

    # 4. Exception Handling Tests

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    def test_document_generation_raises_exception(self, mock_fill_docs):
        """Test handling when document generation raises an exception."""
        mock_fill_docs.side_effect = Exception("Document generation error")

        with self.assertRaises(Exception):
            self._call_command()

        # Verify plan was not marked as sent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    def test_document_sending_raises_exception(self, mock_fill_docs, mock_send_docs):
        """Test handling when document sending raises an exception."""
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.side_effect = Exception("Sending error")

        with self.assertRaises(Exception):
            self._call_command()

        # Verify plan was not marked as sent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    def test_plan_save_raises_exception(self, mock_fill_docs, mock_send_docs):
        """Test handling when plan.save() raises an exception."""
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = True

        # Mock the save method to raise an exception
        with mock.patch.object(
            RiskPreventionPlan, "save", side_effect=Exception("Save error")
        ):
            with self.assertRaises(Exception):
                self._call_command()

    # 5. Sentry Integration Tests

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_sentry_extras_set_correctly(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test that Sentry extras are set correctly for each plan."""
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = True

        self._call_command()

        # Verify sentry extras were set
        mock_sentry.set_extra.assert_any_call("user", self.user.email)
        mock_sentry.set_extra.assert_any_call("run", self.run.id)

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_sentry_capture_message_on_document_generation_failure(
        self, mock_sentry, mock_fill_docs
    ):
        """Test Sentry message capture on document generation failure."""
        mock_fill_docs.return_value = None

        self._call_command()

        mock_sentry.capture_message.assert_called_once_with(
            "Failed to generate radiation protection document", level="error"
        )

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_sentry_capture_message_on_document_sending_failure(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test Sentry message capture on document sending failure."""
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = False

        self._call_command()

        mock_sentry.capture_message.assert_called_once_with(
            "Failed to send radiation protection document to risk advisor",
            level="error",
        )

    # 6. Output Message Tests

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    def test_stdout_messages_correct_format(self, mock_fill_docs, mock_send_docs):
        """Test that stdout messages have correct format."""
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = True

        out, _ = self._call_command()

        # Verify message format
        self.assertIn(
            "[send-risk-prevention-plans] Sending risk prevention plans to risk advisor...",  # pylint: disable=line-too-long
            out,
        )
        self.assertIn(
            "[send-risk-prevention-plans] Found 1 risk prevention plans to process.",
            out,
        )
        self.assertIn(
            f"[send-risk-prevention-plans] Successfully generated and sent radiation protection document for user {self.user.email}",  # pylint: disable=line-too-long
            out,
        )

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    def test_stderr_messages_on_errors(self, mock_fill_docs):
        """Test stderr messages on various errors."""
        mock_fill_docs.return_value = None

        _, err = self._call_command()

        # Verify error message format
        self.assertIn(
            f"[send-risk-prevention-plans] Failed to generate radiation protection document for user {self.user.id}",  # pylint: disable=line-too-long
            err,
        )

    # 7. Database State Tests

    def test_only_unsent_plans_processed(self):
        """Test that only unsent plans are processed."""
        # Create a plan that's already been sent
        participation = lab_factories.ParticipationFactory()
        run = lab_factories.RunFactory(project=participation.project)
        sent_plan = RiskPreventionPlan.objects.create(
            participation=participation,
            run=run,
            risk_advisor_notification_sent=True,
        )

        with mock.patch(
            "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
        ) as mock_fill_docs:
            mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]

            out, _ = self._call_command()

            # Should only process the unsent plan
            self.assertIn("Found 1 risk prevention plans to process", out)

            # Verify sent plan remains unchanged
            sent_plan.refresh_from_db()
            self.assertTrue(sent_plan.risk_advisor_notification_sent)

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    def test_plan_marked_sent_after_success(self, mock_fill_docs, mock_send_docs):
        """Test that plan is marked as sent after successful processing."""
        mock_fill_docs.return_value = [("document.pdf", b"pdf_content")]
        mock_send_docs.return_value = True

        # Verify initial state
        self.assertFalse(self.plan.risk_advisor_notification_sent)

        self._call_command()

        # Verify final state
        self.plan.refresh_from_db()
        self.assertTrue(self.plan.risk_advisor_notification_sent)

    @mock.patch(
        # pylint: disable=line-too-long
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"
    )
    def test_plan_not_marked_sent_on_failure(self, mock_fill_docs):
        """Test that plan is not marked as sent on any failure."""
        mock_fill_docs.return_value = None

        # Verify initial state
        self.assertFalse(self.plan.risk_advisor_notification_sent)

        self._call_command()

        # Verify plan remains unsent
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.risk_advisor_notification_sent)

    # 8. Edge Cases and Integration Tests

    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.send_document_to_risk_advisor"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.fill_radiation_protection_documents"  # pylint: disable=line-too-long
    )
    @mock.patch(
        "radiation_protection.management.commands.send_risk_prevention_plans.sentry_sdk"
    )
    def test_mixed_success_and_failure_scenarios(
        self, mock_sentry, mock_fill_docs, mock_send_docs
    ):
        """Test mixed scenarios with some plans succeeding and others failing."""
        # Create multiple plans
        user2 = auth_factories.StaffUserFactory()
        participation2 = lab_factories.ParticipationFactory(
            user=user2, project=self.project, on_premises=True
        )
        plan2 = RiskPreventionPlan.objects.create(
            participation=participation2,
            run=self.run,
            risk_advisor_notification_sent=False,
        )

        user3 = auth_factories.StaffUserFactory()
        participation3 = lab_factories.ParticipationFactory(
            user=user3, project=self.project, on_premises=True
        )
        plan3 = RiskPreventionPlan.objects.create(
            participation=participation3,
            run=self.run,
            risk_advisor_notification_sent=False,
        )

        # Setup mocks for mixed results
        # First call succeeds, second fails at document generation, third would succeed
        mock_fill_docs.side_effect = [
            [("document.pdf", b"pdf_content")],  # Success
            None,  # Failure
            [("document2.pdf", b"pdf_content2")],  # Success
        ]
        mock_send_docs.return_value = True

        self._call_command()

        # Verify mixed results
        self.plan.refresh_from_db()
        plan2.refresh_from_db()
        plan3.refresh_from_db()

        # Count successful plans (should be 2 out of 3)
        successful_plans = sum(
            [
                self.plan.risk_advisor_notification_sent,
                plan2.risk_advisor_notification_sent,
                plan3.risk_advisor_notification_sent,
            ]
        )
        self.assertEqual(successful_plans, 2)

        # Verify one plan failed (plan2 with None documents)
        self.assertFalse(plan2.risk_advisor_notification_sent)

        # Verify error was captured for the failed plan
        mock_sentry.capture_message.assert_called_with(
            "Failed to generate radiation protection document", level="error"
        )
