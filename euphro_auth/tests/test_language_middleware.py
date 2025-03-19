"""Tests for the language middleware and user language preferences."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils import translation

from euphro_auth.middleware import UserLanguageMiddleware

User = get_user_model()


class UserLanguageModelTest(TestCase):
    """Tests for the preferred_language field on User model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

    def test_preferred_language_field_exists(self):
        """Test that the preferred_language field exists and is initially None."""
        self.assertIsNone(self.user.preferred_language)

    def test_preferred_language_can_be_set(self):
        """Test that preferred_language can be set and retrieved."""
        self.user.preferred_language = "en"
        self.user.save()

        # Refresh from database to verify it was saved
        user_from_db = User.objects.get(pk=self.user.pk)
        self.assertEqual(user_from_db.preferred_language, "en")


class UserLanguageMiddlewareTest(TestCase):
    """Tests for the UserLanguageMiddleware."""

    def setUp(self):
        """Set up test data and middleware."""
        self.factory = RequestFactory()
        self.middleware = UserLanguageMiddleware(get_response=MagicMock())
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

    def test_process_request_for_anonymous_user(self):
        """Test that middleware does nothing for anonymous users."""
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=False)

        with patch.object(self.middleware, "_update_user_language") as mock_update:
            self.middleware.process_request(request)
            mock_update.assert_not_called()

    def test_process_request_when_language_matches(self):
        """Test that middleware does nothing when language already matches."""
        request = self.factory.get("/")
        self.user.preferred_language = "en"
        self.user.save()
        request.user = self.user

        with patch("django.utils.translation.get_language", return_value="en"):
            with patch.object(self.middleware, "_update_user_language") as mock_update:
                self.middleware.process_request(request)
                mock_update.assert_not_called()

    def test_process_request_when_language_differs(self):
        """Test that middleware updates language when they differ."""
        request = self.factory.get("/")
        self.user.preferred_language = "en"
        self.user.save()
        request.user = self.user

        with patch("django.utils.translation.get_language", return_value="fr"):
            with patch.object(self.middleware, "_update_user_language") as mock_update:
                self.middleware.process_request(request)
                mock_update.assert_called_once_with(self.user, "fr")

    def test_update_user_language(self):
        """Test that _update_user_language updates the database."""
        self.user.preferred_language = "en"
        self.user.save()

        # We're accessing a protected method in a test, which is acceptable
        # pylint: disable=protected-access
        self.middleware._update_user_language(self.user, "fr")

        # Verify the database was updated
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertEqual(updated_user.preferred_language, "fr")
        # Verify the in-memory object was updated
        self.assertEqual(self.user.preferred_language, "fr")

    @override_settings(LANGUAGE_CODE="fr")
    def test_integration_with_translation(self):
        """Test middleware with Django's translation system."""
        with patch.object(self.middleware, "_update_user_language") as mock_update:
            with translation.override("es"):
                request = self.factory.get("/")
                request.user = self.user

                # Process request should detect the 'es' language
                self.middleware.process_request(request)

                # Verify the language was detected correctly and passed
                mock_update.assert_called_once_with(self.user, "es")

    def test_update_user_language_exception_handling(self):
        """Test that exceptions in _update_user_language are caught."""
        # Force an exception by patching the User.objects.filter method
        model_path = f"{User.__module__}.{User.__name__}.objects.filter"
        with patch(model_path) as mock_filter:
            mock_filter.side_effect = Exception("Database error")

            # Should not raise an exception
            # pylint: disable=protected-access
            self.middleware._update_user_language(self.user, "fr")
