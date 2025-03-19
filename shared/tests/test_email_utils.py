"""Tests for the language-aware email utility."""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import translation
from django.utils.translation import gettext as _

from euphro_auth.models import User
from shared.email_utils import send_email_with_language, use_user_language


class EmailUtilsTests(TestCase):
    """Tests for shared.email_utils module."""

    def setUp(self):
        """Set up test data with users having different language preferences."""
        self.user_en = User.objects.create_user(
            email="english@example.com",
            password="testpassword",
            first_name="English",
            last_name="User",
            preferred_language="en",
        )
        self.user_fr = User.objects.create_user(
            email="french@example.com",
            password="testpassword",
            first_name="French",
            last_name="User",
            preferred_language="fr",
        )
        self.user_no_pref = User.objects.create_user(
            email="default@example.com",
            password="testpassword",
            first_name="Default",
            last_name="User",
        )

    def test_use_user_language_context_manager(self):
        """Test that the context manager correctly activates user's language."""
        # Make sure we start with a different language
        translation.activate("fr")

        # Test with a user with English preference
        with use_user_language(self.user_en):
            self.assertEqual(translation.get_language(), "en")

        # Test language was restored
        self.assertEqual(translation.get_language(), "fr")

        # Test with a user with French preference
        with use_user_language(self.user_fr):
            self.assertEqual(translation.get_language(), "fr")

        # Test with a user with no preference - should keep current language
        with use_user_language(self.user_no_pref):
            self.assertEqual(translation.get_language(), "fr")

        # Test with explicit fallback language
        with use_user_language(self.user_no_pref, language_code="en"):
            self.assertEqual(translation.get_language(), "en")

        # Test with no user but with fallback language
        with use_user_language(language_code="en"):
            self.assertEqual(translation.get_language(), "en")

    @patch("shared.email_utils.loader")
    @patch("shared.email_utils.EmailMultiAlternatives")
    def test_send_email_with_language(self, mock_email_multi, mock_loader):
        """Test that send_email_with_language respects user's language preference."""
        # Setup mocks
        mock_email_instance = MagicMock()
        mock_email_multi.return_value = mock_email_instance
        mock_loader.render_to_string.return_value = "Test content"

        # Test with English-preferring user
        subject = _("Welcome to Euphrosyne")
        context = {"name": "Test"}

        # Store current translations for testing
        with translation.override("en"):
            english_subject = str(subject)
        with translation.override("fr"):
            french_subject = str(subject)

        # Send email to English user
        send_email_with_language(
            subject=subject,
            template_name="test_template",
            context=context,
            to_emails=["english@example.com"],
            user=self.user_en,
        )

        # Check that email was created with English subject
        mock_email_multi.assert_called_with(
            subject=english_subject, body="Test content", to=["english@example.com"]
        )

        # Send email to French user
        send_email_with_language(
            subject=subject,
            template_name="test_template",
            context=context,
            to_emails=["french@example.com"],
            user=self.user_fr,
        )

        # Check that email was created with French subject
        mock_email_multi.assert_called_with(
            subject=french_subject, body="Test content", to=["french@example.com"]
        )
