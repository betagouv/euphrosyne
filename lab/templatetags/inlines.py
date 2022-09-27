import json

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def update_inline_formset_data_add_text(inline_formset_data: str, value):
    data = json.loads(inline_formset_data)
    if "options" in data:
        data["options"]["addText"] = str(value)
    return json.dumps(data)
