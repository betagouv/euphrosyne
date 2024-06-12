import json

from django import template
from django.contrib.admin.helpers import AdminReadonlyField
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def update_inline_formset_data_add_text(inline_formset_data: str, value):
    data = json.loads(inline_formset_data)
    if "options" in data:
        data["options"]["addText"] = str(value)
    return json.dumps(data)


@register.filter
def get_contents_for_readonly_field(field: AdminReadonlyField):
    """Get the content for a readonly field.
    If it is a ForeignKey, return in priority the string representation
    of the related object, to avoid seeing links to the related object.
    """
    if field.form.instance and hasattr(field.form.instance, field.field["field"]):
        return str(getattr(field.form.instance, field.field["field"]))
    return field.contents()
