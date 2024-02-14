from django import template

register = template.Library()


@register.inclusion_tag("django/forms/widgets/attrs.html", takes_context=True)
def attrs_with_dsfr(context):
    if "widget" in context and "attrs" in context["widget"]:
        # add the dsfr class to the widget
        context["widget"]["attrs"]["class"] = (
            context["widget"]["attrs"].get("class", "") + " fr-input"
        )
    return context
