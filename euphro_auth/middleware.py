from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction


class UserLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to compare user's preferred language from the request with stored preference
    and update it if different.
    """
    
    def process_request(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
            
        # Get the current language from Django's translation
        current_language = translation.get_language()
        
        # Check if we need to update user's preferred language
        if current_language and request.user.preferred_language != current_language:
            # Update user language directly, but efficiently
            self._update_user_language(request.user, current_language)
            
        return None
    
    def _update_user_language(self, user, language):
        """
        Update the user's preferred language in the database
        
        This uses a direct SQL update when possible to minimize overhead.
        """
        # Import inside method to avoid circular imports
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            # Use a direct update query for better performance
            # This avoids loading the full User object and triggering signals
            User.objects.filter(pk=user.pk).update(preferred_language=language)
            
            # Update the current instance in memory to maintain consistency
            user.preferred_language = language
        except Exception:
            # Fail silently to avoid affecting the request
            # In production, this should be logged properly
            pass