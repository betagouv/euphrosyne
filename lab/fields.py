from typing import Any, Dict, List, Optional

from django.forms.fields import Field, IntegerField
from django.forms.widgets import Widget
from django.utils import formats

from .widgets import MultiDatalistWidget


class MultiDatalistIntegerField(IntegerField):
    widget = MultiDatalistWidget

    def to_python(self, value: Optional[List[int]]) -> Optional[int]:
        # [XXX] Raincoat: django/forms/fields.py:277
        value = Field.to_python(self, value)
        if value in self.empty_values:
            return None
        if self.localize:
            value = formats.sanitize_separators(value)
        return value
