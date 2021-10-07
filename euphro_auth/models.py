from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

from .managers import UserManager


class UserGroups(Enum):
    ADMIN = "Admin"


class User(AbstractUser):
    """Custom User model for authentication with email as identifier."""

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [f for f in AbstractUser.REQUIRED_FIELDS if f != "email"]

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)
    username = None
    invitation_completed = models.BooleanField(_("invitation completed"), default=False)

    objects = UserManager()

    def __str__(self):
        return self.email

    def delete(self, *_):
        self.is_active = False
        self.save()


class UserInvitation(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
