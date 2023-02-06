from django.forms.widgets import Select

from .types import OTHER_VALUE


class SelectWithFreeOther(Select):
    template_name = "forms/widgets/selectwithfree.html"
    option_template_name = "forms/widgets/selectwithfree_option.html"

    class Media:
        js = ("js/widgets/select-with-free-other.js",)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["OTHER_VALUE"] = OTHER_VALUE
        if isinstance(value, list):
            # pylint: disable=broad-exception-raised
            raise Exception("List value")
        context["widget"]["value_is_other"] = value not in [c[0] for c in self.choices]
        return context
