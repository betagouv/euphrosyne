from unittest.mock import patch, MagicMock
import asyncio

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.utils import translation

from euphro_auth.middleware import UserLanguageMiddleware

User = get_user_model()


class UserLanguageModelTest(TestCase):
    """Tests for the preferred_language field on User model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

    def test_preferred_language_field_exists(self):
        """Test that the preferred_language field exists and is initially None"""
        self.assertIsNone(self.user.preferred_language)
    
    def test_preferred_language_can_be_set(self):
        """Test that preferred_language can be set and retrieved"""
        self.user.preferred_language = "en"
        self.user.save()
        
        # Refresh from database to verify it was saved
        user_from_db = User.objects.get(pk=self.user.pk)
        self.assertEqual(user_from_db.preferred_language, "en")


class UserLanguageMiddlewareTest(TestCase):
    """Tests for the UserLanguageMiddleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = UserLanguageMiddleware(get_response=MagicMock())
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )
        
    def test_process_request_for_anonymous_user(self):
        """Test that middleware does nothing for anonymous users"""
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        
        with patch.object(self.middleware, '_schedule_language_update') as mock_schedule:
            self.middleware.process_request(request)
            mock_schedule.assert_not_called()
    
    def test_process_request_when_language_matches(self):
        """Test that middleware does nothing when language already matches"""
        request = self.factory.get("/")
        self.user.preferred_language = "en"
        self.user.save()
        request.user = self.user
        
        with patch('django.utils.translation.get_language', return_value="en"):
            with patch.object(self.middleware, '_schedule_language_update') as mock_schedule:
                self.middleware.process_request(request)
                mock_schedule.assert_not_called()
    
    def test_process_request_when_language_differs(self):
        """Test that middleware schedules update when languages differ"""
        request = self.factory.get("/")
        self.user.preferred_language = "en"
        self.user.save()
        request.user = self.user
        
        with patch('django.utils.translation.get_language', return_value="fr"):
            with patch.object(self.middleware, '_schedule_language_update') as mock_schedule:
                self.middleware.process_request(request)
                mock_schedule.assert_called_once_with(self.user, "fr")
    
    @patch('asyncio.create_task')
    def test_schedule_language_update(self, mock_create_task):
        """Test that _schedule_language_update creates a task"""
        self.middleware._schedule_language_update(self.user, "fr")
        
        # Check that create_task was called (exact arguments are hard to check)
        mock_create_task.assert_called_once()
    
    @override_settings(LANGUAGE_CODE='fr')
    @patch('euphro_auth.middleware.UserLanguageMiddleware._update_user_language')
    def test_integration_with_translation(self, mock_update):
        """Test middleware with Django's translation system"""
        # Set up mock for the async update method
        async def mock_coro(*args, **kwargs):
            pass
        mock_update.return_value = mock_coro()
        
        with translation.override('es'):
            request = self.factory.get("/")
            request.user = self.user
            
            # Process request should detect the 'es' language
            self.middleware.process_request(request)
            
            # The event loop and async machinery make this test complex,
            # but we can at least verify the initial call was made correctly
            mock_update.assert_called_once()
            # First argument is a SimpleLazyObject, second should be 'es'
            self.assertEqual(mock_update.call_args[0][1], 'es')


# This test requires running with asyncio support
class AsyncUserLanguageMiddlewareTest(TestCase):
    """Tests for the asynchronous update functionality of UserLanguageMiddleware"""
    
    async def test_update_user_language(self):
        """Test the async method to update user language"""
        # Create a user
        user = await User.objects.acreate(
            email="async@example.com",
            password="testpassword",
            first_name="Async",
            last_name="User",
        )
        
        # Call the async update method
        await UserLanguageMiddleware._update_user_language(user, "de")
        
        # Verify the user was updated
        user_from_db = await User.objects.aget(pk=user.pk)
        self.assertEqual(user_from_db.preferred_language, "de")
        
        # Cleanup
        await user.adelete()