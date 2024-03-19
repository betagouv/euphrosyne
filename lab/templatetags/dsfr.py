from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag("django/forms/widgets/attrs.html", takes_context=True)
def attrs_with_dsfr(context):
    if "widget" in context and "attrs" in context["widget"]:
        # add the dsfr class to the widget
        classes_to_add = []
        widget = context["widget"]
        if "select.html" in widget["template_name"]:
            classes_to_add.append("fr-select")
        else:
            classes_to_add.append("fr-input")
        context["widget"]["attrs"]["class"] = (
            widget["attrs"].get("class", "") + " " + " ".join(classes_to_add)
        )
    return context


@register.simple_tag
def label_tag_with_dsfr(label_html: str):
    return mark_safe(label_html.replace("<label", '<label class="fr-label"'))
