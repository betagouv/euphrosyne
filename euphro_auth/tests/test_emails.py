"""Tests for email sending functionality."""

from unittest.mock import patch

from django.core import mail
from django.test import SimpleTestCase, TestCase
from django.utils.translation import gettext

from euphro_auth.models import User

from ..emails import send_invitation_email


class InvitationEmailTests(SimpleTestCase):
    """Tests for the basic invitation email functionality."""

    def test_send_email(self):
        """Test that the invitation email is sent with the correct content."""
        send_invitation_email(user=User(id=1, email="test@test.com"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, gettext("[Euphrosyne] Invitation to register")
        )
        self.assertRegex(mail.outbox[0].body, r"\/registration\/MQ\/.{39,45}\/")


class LanguageAwareEmailTests(TestCase):
    """Tests for language-aware email sending."""

    def setUp(self):
        """Set up test data with a user having French language preference."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
            preferred_language="fr",  # Set preferred language to French
        )

    @patch("euphro_auth.emails.send_email_with_language")
    def test_send_invitation_email_respects_language(self, mock_send_email):
        """Test that send_invitation_email respects the user's preferred language."""
        # Call the send_invitation_email function
        send_invitation_email(self.user)

        # Verify send_email_with_language was called with the correct parameters
        mock_send_email.assert_called_once()
        # Check that user is passed to respect language preference
        args, kwargs = mock_send_email.call_args
        self.assertEqual(kwargs["user"], self.user)
        self.assertEqual(kwargs["to_emails"], [self.user.email])

        # The context should include the necessary tokens
        self.assertIn("token", kwargs["context"])
        self.assertIn("uid", kwargs["context"])
        self.assertIn("email", kwargs["context"])
        self.assertIn("site_url", kwargs["context"])
