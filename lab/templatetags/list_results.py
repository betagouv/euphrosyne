import html
import re
import unicodedata
from typing import Optional

from django import template

register = template.Library()


def strip_accents(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def get_class_name(text):
    return strip_accents(text).replace(" ", "-").lower()


class PrettyStatusNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        output_unescaped = html.unescape(output)
        if 'class="field-status"' in output_unescaped:
            return re.sub(
                r">(.*?)<",
                lambda m: (
                    fr'><span class="fr-tag {get_class_name(m.group(1))}">'
                    fr"{m.group(1)}"
                    "</span><"
                ),
                output_unescaped,
            )

        return output


@register.tag
def prettify(parser, token):
    nodelist = parser.parse(("endprettify",))
    parser.delete_first_token()
    return PrettyStatusNode(nodelist)
