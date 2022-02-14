import html

from django.template import Context, Template


def test_prettify_tag_doesnt_change_random_field():
    template = Template(
        "{% load list_results %}{% prettify %}{{ item }}{% endprettify %}"
    )
    item_html = '<td class="field-whatever">A planifier</td>'
    context = Context({"item": item_html})
    assert html.unescape(template.render(context)) == item_html


def test_prettify_tag_changes_field_status():
    template = Template(
        "{% load list_results %}{% prettify %}{{ item }}{% endprettify %}"
    )
    item_html = '<td class="field-status">à planifier comme ça</td>'
    context = Context({"item": item_html})
    assert html.unescape(template.render(context)) == (
        '<td class="field-status"><span class="a-planifier-comme-ca">'
        "à planifier comme ça"
        "</span></td>"
    )
