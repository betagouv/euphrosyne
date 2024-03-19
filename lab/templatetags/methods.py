from django import template
from django.template.loader import get_template

from ..methods.templatetags import (  # pylint: disable=unused-import # noqa: F401
    _get_adminfield_name,
    detector_fields,
    filters_field,
    method_fields,
    run_methods_repr,
)

register = template.Library()

register.filter(method_fields)
register.filter(detector_fields)
register.filter(filters_field)

register.inclusion_tag(get_template("run_methods_repr.html"))(run_methods_repr)
