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
    username = None

    invitation_completed_at = models.DateTimeField(
        _("invitation completed at"), blank=True, null=True
    )
    is_lab_admin = models.BooleanField(_("is Euphrosyne admin"), default=False)

    objects = UserManager()

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
