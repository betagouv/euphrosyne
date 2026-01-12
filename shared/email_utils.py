import logging
import smtplib
from contextlib import contextmanager

from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils import translation

logger = logging.getLogger(__name__)


@contextmanager
def use_user_language(user=None, language_code=None):
    """
    Context manager that activates the user's preferred language for the duration
    of the context. Falls back to the provided language_code or the default language.

    Usage:
        with use_user_language(user):
            # Code here will use the user's preferred language
            subject = _("Welcome")
    """
    current_language = translation.get_language()

    try:
        if user and user.preferred_language:
            # Use the user's preferred language if available
            translation.activate(user.preferred_language)
        elif language_code:
            # Fall back to the provided language code
            translation.activate(language_code)
        # If neither is provided, maintain the current language

        yield
    finally:
        # Restore the previous language
        translation.activate(current_language)


# pylint: disable=too-many-arguments
def send_email_with_language(
    subject, template_name, context, to_emails, user=None, language_code=None
):
    """
    Send an email respecting the user's preferred language.

    Args:
        subject: Email subject (must already be translated in preferred language)
        template_name: Base template name (without extension)
        context: Context for the email templates
        to_emails: List of recipient email addresses
        user: User object to get language preference from
        language_code: Fallback language code if user has no preference
    """
    with use_user_language(user, language_code):
        translated_subject = str(subject)

        # Render templates in the user's preferred language
        text_body = loader.render_to_string(f"{template_name}.txt", context)
        html_body = loader.render_to_string(f"{template_name}.html", context)

        # Create email message
        email_message = EmailMultiAlternatives(
            subject=translated_subject, body=text_body, to=to_emails
        )
        email_message.attach_alternative(html_body, "text/html")

        try:
            email_message.send()
            return True
        except (smtplib.SMTPException, ConnectionError) as e:
            logger.error(
                "Error sending email to %s. Reason: %s",
                to_emails,
                str(e),
            )
            return False
