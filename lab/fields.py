from typing import List, Optional

from django.forms.fields import Field, IntegerField
from django.utils import formats

from .widgets import MultiDatalistWidget


class MultiDatalistIntegerField(IntegerField):
    widget = MultiDatalistWidget

    def to_python(self, value: Optional[List[int]]) -> Optional[int]:
        # pylint: disable=line-too-long
        # Raincoat: pypi package: django==4.0a1 path: django/forms/fields.py element: IntegerField.to_python
        value = Field.to_python(self, value)
        if value in self.empty_values:
            return None
        if self.localize:
            value = formats.sanitize_separators(value)
        return value
