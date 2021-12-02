from django import template

from ..methods.templatetags import (  # pylint: disable=unused-import # noqa: F401
    _get_adminfield_name,
    detector_fields,
    filters_field,
    method_fields,
)

register = template.Library()

register.filter(method_fields)
register.filter(detector_fields)
register.filter(filters_field)
