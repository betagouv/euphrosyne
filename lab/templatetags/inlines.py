import json

from django import template

register = template.Library()


@register.filter
def update_inline_formset_data_add_text(inline_formset_data: str, value: str):
    data = json.loads(inline_formset_data)
    if "options" in data:
        data["options"]["addText"] = value
    return json.dumps(data)
