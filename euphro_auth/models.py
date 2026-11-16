from django.contrib.auth.models import AbstractUser
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from shared.names import normalize_person_name

from .managers import UserManager

EMAIL_ALREADY_EXISTS = "email_already_exists"


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

    class Meta(AbstractUser.Meta):
        constraints = [
            # allauth matches emails case-insensitively (login, password reset).
            models.UniqueConstraint(
                Lower("email"),
                name="euphro_auth_user_email_ci_unique",
                violation_error_message=_("An account with this email already exists."),
                violation_error_code=EMAIL_ALREADY_EXISTS,
            ),
        ]

    def __str__(self):
        return (
            f"{self.last_name}, {self.first_name}<{self.email}>"
            if (self.last_name and self.first_name)
            else self.email
        )

    def delete(self, *_):
        self.is_active = False
        self.save()

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields is None:
            # Full save: normalize the email and both names.
            self.email = UserManager.normalize_email(self.email)
            self.first_name = normalize_person_name(self.first_name)
            self.last_name = normalize_person_name(self.last_name)
        else:
            # Partial update: only normalize fields that will be saved.
            if "email" in update_fields:
                self.email = UserManager.normalize_email(self.email)
            if "first_name" in update_fields:
                self.first_name = normalize_person_name(self.first_name)
            if "last_name" in update_fields:
                self.last_name = normalize_person_name(self.last_name)
        super().save(*args, **kwargs)

    def validate_unique(self, exclude=None):
        # The case-insensitive constraint covers the email, and reports a
        # conflict once instead of also failing on the exact unique index.
        super().validate_unique(exclude={*(exclude or ()), "email"})

    def validate_constraints(self, exclude=None):
        try:
            super().validate_constraints(exclude=exclude)
        except ValidationError as error:
            # Show the email conflict next to the field, not above the form.
            errors = error.update_error_dict({})
            other_errors = []
            for item in errors.pop(NON_FIELD_ERRORS, []):
                if getattr(item, "code", None) == EMAIL_ALREADY_EXISTS:
                    errors.setdefault("email", []).append(item)
                else:
                    other_errors.append(item)
            if other_errors:
                errors[NON_FIELD_ERRORS] = other_errors
            raise ValidationError(errors) from error

    def get_administrative_name(self) -> str:
        full_name = "%s %s" % (self.last_name.upper(), self.first_name)
        return full_name.strip()


class UserInvitation(User):
    class Meta:
        proxy = True
        verbose_name = _("User invitation")
        verbose_name_plural = _("User invitations")

    def clean(self):
        super().clean()
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
