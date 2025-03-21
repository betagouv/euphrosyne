from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """Custom User model for authentication with email as identifier."""

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [f for f in AbstractUser.REQUIRED_FIELDS if f != "email"]

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)
    username = None  # type: ignore[assignment]
    preferred_language = models.CharField(
        _("preferred language"), max_length=10, blank=True, null=True
    )

    invitation_completed_at = models.DateTimeField(
        _("invitation completed at"), blank=True, null=True
    )
    is_lab_admin = models.BooleanField(_("is Euphrosyne admin"), default=False)

    cgu_accepted_at = models.DateTimeField(_("CGU accepted at"), blank=True, null=True)

    objects = UserManager()  # type: ignore

    def __str__(self):
        return (
            f"{self.last_name}, {self.first_name}<{self.email}>"
            if (self.last_name and self.first_name)
            else self.email
        )

    def delete(self, *_):
        self.is_active = False
        self.save()


class UserInvitation(User):
    class Meta:
        proxy = True
        verbose_name = _("User invitation")
        verbose_name_plural = _("User invitations")

    def clean(self):
        if not self.pk:
            self.is_staff = True

    @classmethod
    def create_user(cls, **attributes):
        """Create a new user and send an invitation."""
        # pylint: disable=import-outside-toplevel
        from euphro_auth.emails import send_invitation_email

        user = cls.objects.create(**attributes, is_staff=True)
        send_invitation_email(user)
        return user
