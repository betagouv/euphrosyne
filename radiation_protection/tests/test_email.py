from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings

from euphro_auth.tests import factories as auth_factories
from radiation_protection.email import notify_additional_emails


class TestNotifyAdditionalEmails(TestCase):
    """Test cases for notify_additional_emails function."""

    def setUp(self):
        """Set up test data."""
        self.user = auth_factories.StaffUserFactory(
            first_name="John", last_name="Doe", email="john.doe@example.com"
        )

    @override_settings(RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=None)
    def test_no_additional_emails_configured(self):
        """Test that function returns early when no additional emails are configured."""
        notify_additional_emails(self.user)

        # No emails should be sent
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=[])
    def test_empty_additional_emails_list(self):
        """Test that function returns early when additional emails list is empty."""
        notify_additional_emails(self.user)

        # No emails should be sent
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=[
            "admin@example.com",
            "security@example.com",
        ],
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_successful_email_notification(self):
        """Test successful email notification to additional emails."""
        notify_additional_emails(self.user)

        # One email should be sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(
            email.subject, "Nouveau certificat de formation aux risques pour John Doe"
        )
        self.assertEqual(email.from_email, "noreply@example.com")
        self.assertEqual(email.to, ["admin@example.com", "security@example.com"])

        # Check email body contains expected content
        self.assertIn("John Doe", email.body)
        self.assertIn("vient d'obtenir son certificat", email.body)
        self.assertIn("formation aux risques présents à AGLAE", email.body)
        self.assertIn("Euphrosyne", email.body)

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=["test@example.com"],
        DEFAULT_FROM_EMAIL="sender@example.com",
    )
    def test_email_content_with_user_without_last_name(self):
        """Test email content when user has no last name."""
        user = auth_factories.StaffUserFactory(
            first_name="Jane", last_name="", email="jane@example.com"
        )

        notify_additional_emails(user)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(
            email.subject, "Nouveau certificat de formation aux risques pour Jane"
        )
        self.assertIn("Jane", email.body)

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=["test@example.com"],
        DEFAULT_FROM_EMAIL="sender@example.com",
    )
    def test_email_content_with_user_without_first_name(self):
        """Test email content when user has no first name."""
        user = auth_factories.StaffUserFactory(
            first_name="", last_name="Smith", email="smith@example.com"
        )

        notify_additional_emails(user)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(
            email.subject, "Nouveau certificat de formation aux risques pour Smith"
        )
        self.assertIn("Smith", email.body)

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=["test@example.com"],
        DEFAULT_FROM_EMAIL="sender@example.com",
    )
    def test_email_content_with_user_without_names(self):
        """Test email content when user has no first or last name."""
        user = auth_factories.StaffUserFactory(
            first_name="", last_name="", email="anonymous@example.com"
        )

        notify_additional_emails(user)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        # get_full_name() returns empty string when both names are empty
        self.assertEqual(
            email.subject, "Nouveau certificat de formation aux risques pour "
        )

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=["test@example.com"]
    )
    @mock.patch("radiation_protection.email.EmailMessage.send")
    @mock.patch("radiation_protection.email.logger")
    def test_email_send_failure_logs_error(self, mock_logger, mock_send):
        """Test that email send failures are logged properly."""
        mock_send.side_effect = Exception("SMTP server error")

        notify_additional_emails(self.user)

        # Verify error was logged
        mock_logger.error.assert_called_once()
        args = mock_logger.error.call_args[0]
        self.assertIn("Failed to notify additional emails", args[0])
        self.assertIn("radiation protection document", args[0])
        self.assertEqual(args[1], self.user.id)
        self.assertEqual(args[2], "SMTP server error")

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=["test@example.com"]
    )
    @mock.patch("radiation_protection.email.EmailMessage")
    @mock.patch("radiation_protection.email.logger")
    def test_email_creation_failure_logs_error(self, mock_logger, mock_email_class):
        """Test that email creation failures are logged properly."""
        mock_email_class.side_effect = Exception("Email creation failed")

        notify_additional_emails(self.user)

        # Verify error was logged
        mock_logger.error.assert_called_once()
        args = mock_logger.error.call_args[0]
        self.assertIn("Failed to notify additional emails", args[0])
        self.assertIn("radiation protection document", args[0])
        self.assertEqual(args[1], self.user.id)
        self.assertEqual(args[2], "Email creation failed")

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=["admin@example.com"]
    )
    def test_email_multipart_structure(self):
        """Test that EmailMessage is used correctly."""
        notify_additional_emails(self.user)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verify it's an EmailMessage
        self.assertIsInstance(email, mail.EmailMessage)

        # Verify email structure
        self.assertTrue(email.subject)
        self.assertTrue(email.body)
        self.assertEqual(email.to, ["admin@example.com"])

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=[
            "test1@example.com",
            "test2@example.com",
        ]
    )
    def test_multiple_recipients(self):
        """Test sending email to multiple recipients."""
        notify_additional_emails(self.user)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.to), 2)
        self.assertIn("test1@example.com", email.to)
        self.assertIn("test2@example.com", email.to)

    @override_settings(
        RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS=["test@example.com"]
    )
    def test_email_body_formatting(self):
        """Test that email body is properly formatted."""
        notify_additional_emails(self.user)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Check body contains expected French text
        self.assertIn("Bonjour,", email.body)
        self.assertIn("vient d'obtenir son certificat", email.body)
        self.assertIn("formation aux risques présents à AGLAE", email.body)
        self.assertIn("Bisous", email.body)
        self.assertIn("Euphrosyne", email.body)

        # Check that the body contains the user's full name
        self.assertIn(self.user.get_full_name(), email.body)
