from django.contrib.auth.password_validation import MinimumLengthValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .models import User


class UserMinimumLengthValidator(MinimumLengthValidator):
    def __init__(self):
        super().__init__(min_length=12)


class AdminMinimumLengthValidator(MinimumLengthValidator):
    def __init__(self):
        super().__init__(min_length=16)

    def validate(self, password: str, user: User | None = None) -> None:
        if user and (user.is_superuser or user.is_lab_admin):
            super().validate(password, user)

    def get_help_text(self) -> str:
        return ""


class CharacterTypesValidator:
    special_characters = "#?!@$%^&*-'+()_[]"

    # Django's password validator interface supplies the user argument.
    # pylint: disable=unused-argument
    def validate(self, password: str, user: User | None = None) -> None:
        if not (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdecimal() for char in password)
            and any(char in self.special_characters for char in password)
        ):
            raise ValidationError(
                self.get_help_text(),
                code="password_missing_character_types",
            )

    def get_help_text(self) -> str:
        return _(
            "Your password must contain at least one lowercase letter, "
            "one uppercase letter, one digit and one special character "
            "from this list: %(characters)s."
        ) % {"characters": self.special_characters}
