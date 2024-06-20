import pytest
from django.forms import ValidationError

from lab.validators import valid_filename


@pytest.mark.parametrize(
    "name_to_validate,is_valid",
    (
        ("valid name", True),
        ("invalid/name", False),
        ("still...invalid", False),
        ("hyphens-are-ok", True),
        ("underscores_too", True),
        ("1-2_3", True),
        ("o|4|4", False),
        ("\\escaped", False),
    ),
)
def test_valid_filename_validator(name_to_validate: str, is_valid: bool):
    if not is_valid:
        with pytest.raises(ValidationError):
            valid_filename(name_to_validate)
    else:
        assert valid_filename(name_to_validate) is None  # type: ignore[func-returns-value] # pylint: disable=line-too-long
