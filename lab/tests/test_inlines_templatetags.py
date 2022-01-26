import html
import json

from django.template import Context, Template


def test_update_inline_formset_data_add_text():
    inline_formset_data = {
        "name": "#Model_inline",
        "options": {
            "prefix": "Model_inline",
            "addText": "A text to change",
            "deleteText": "Delete",
        },
    }
    template = Template(
        (
            "{% load inlines %}"
            "{{ inline_formset_data|update_inline_formset_data_add_text:"
            '"An updated text that looks good" }}'
        )
    )
    context = Context({"inline_formset_data": json.dumps(inline_formset_data)})
    assert (
        json.loads(html.unescape(template.render(context)))["options"]["addText"]
        == "An updated text that looks good"
    )
