from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

valid_filename = RegexValidator(
    r"^[\w\- ]+$",
    message=_("Only alphanumeric, underscore, hyphen and space characters are allowed"),
)
