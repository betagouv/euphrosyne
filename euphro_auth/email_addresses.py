from allauth.account.models import EmailAddress

from .models import User


def remove_stale_email_addresses(sender, instance: User, **kwargs) -> None:
    # pylint: disable=unused-argument
    """Keep User.email as the only address of an account.

    allauth records addresses in its own table (for example when it builds a
    password reset token) and also accepts them for login and password reset.
    An address replaced in the user admin must not keep working."""
    EmailAddress.objects.filter(user=instance).exclude(
        email__iexact=instance.email
    ).delete()
