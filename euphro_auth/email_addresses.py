from allauth.account.models import EmailAddress

from .models import User

_LOADED_EMAIL = "_email_addresses_loaded_email"


def remember_loaded_email(sender, instance: User, **kwargs) -> None:
    # pylint: disable=unused-argument
    """Record the email an instance was built with, to detect a change on save.
    Read from __dict__: accessing a deferred field would query the database."""
    setattr(instance, _LOADED_EMAIL, instance.__dict__.get("email"))


def remove_stale_email_addresses(
    sender, instance: User, created: bool, update_fields=None, **kwargs
) -> None:
    # pylint: disable=unused-argument
    """Keep User.email as the only address of an account.

    allauth records addresses in its own table (for example when it builds a
    password reset token) and also accepts them for login and password reset.
    An address replaced in the user admin must not keep working.

    Runs only when the email may have changed, not on every save such as the
    last_login update at each sign-in."""
    loaded_email = getattr(instance, _LOADED_EMAIL, None)
    setattr(instance, _LOADED_EMAIL, instance.email)
    if created or (update_fields is not None and "email" not in update_fields):
        return
    if loaded_email is not None and loaded_email == instance.email:
        return
    EmailAddress.objects.filter(user=instance).exclude(
        email__iexact=instance.email
    ).delete()
