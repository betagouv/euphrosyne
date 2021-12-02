"""
Use the decorator to wrap the ModelForm.
Useful to have two fields play together: one controller, one controlled.
Controlled field must be a nullable integer field.
Controller must be a text field rendered as a select.
"""
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from django.forms.fields import Field, IntegerField
from django.forms.models import ModelFormMetaclass
from django.forms.widgets import MultiWidget, Select, Widget
from django.utils import formats


class Datalist(Select):
    """Widget that generates an <input> with an associated <datalist>
    See https://developer.mozilla.org/en-US/docs/Web/HTML/Element/datalist
    """

    input_type = "text"
    template_name = "forms/widgets/datalist.html"
    option_template_name = "forms/widgets/datalist_option.html"
    add_id_index = False
    checked_attribute = {"selected": True}
    option_inherits_attrs = False

    def get_context(self, name, value, attrs):
        attrs_without_id = {k: v for k, v in attrs.items() if k != "id"}
        context = super().get_context(name, value, attrs_without_id)
        context["widget"]["list_id"] = attrs["id"]
        context["widget"]["type"] = "text"
        return context


class ControlledDatalistsWidget(MultiWidget):
    """Contains controlled datalist sub-widgets
    Control which one is shown based on a controlled field value, using
    javascript.
    """

    template_name = "forms/widgets/controlled_datalists.html"

    controller_field_name: str
    controlled_field_name: str

    def __init__(
        self,
        controller_field_name: str,
        controlled_field_name: str,
        widgets: Sequence[Union[Widget, Type[Widget]]],
        attrs: Optional[Any] = None,
    ) -> None:
        super().__init__(widgets, attrs)
        self.controller_field_name = controller_field_name
        self.controlled_field_name = controlled_field_name

    def get_context(
        self, name: str, value: Any, attrs: Optional[Any]
    ) -> Dict[str, Any]:
        context = super().get_context(name, value, attrs)
        context["widget"]["controller_field_name"] = self.controller_field_name
        context["widget"]["controlled_name_prefix"] = f"{self.controlled_field_name}_"
        return context

    def decompress(self, value: Any) -> Optional[Any]:
        """Fill the backend value into all sub-widets at init"""
        return [value] * len(self.widgets)


class MultiDatalistIntegerField(IntegerField):
    """Field based on ControlledDatalistWidget, keeping the form data as a list"""

    widget = ControlledDatalistsWidget

    def to_python(self, value: Optional[List[int]]) -> Optional[int]:
        # pylint: disable=line-too-long
        # Raincoat: pypi package: django==4.0a1 path: django/forms/fields.py element: IntegerField.to_python
        value = Field.to_python(self, value)
        if value in self.empty_values:
            return None
        if self.localize:
            value = formats.sanitize_separators(value)
        return value


def controlled_datalist_form(
    controller_field_name: str,
    controlled_field_name: str,
    choices: Dict[str, List[Tuple[str, str]]],
):
    """Decorator to wrap a ModelForm class with a controller field and a
    controlled integer field with choices displayed in <datalist> elements

    The controller field value will toggle the right datalist in the front-end.
    """

    def wrap_in_subclass(cls):
        def clean(self):  # pylint: disable=unused-argument
            """Reduce: pick the right controlled value based on the controller value"""
            controller_cleaned_value = self.cleaned_data.get(controller_field_name)
            controlled_cleaned_values = self.cleaned_data.get(controlled_field_name)
            if not controller_cleaned_value:
                self.cleaned_data[controlled_field_name] = None
            else:
                self.cleaned_data[controlled_field_name] = (
                    controlled_cleaned_values[
                        list(choices.keys()).index(controller_cleaned_value)
                    ]
                    or None
                )
            return cls.clean(self)

        if cls.Meta.fields == "__all__":

            class Meta(cls.Meta):
                pass

        else:

            class Meta(cls.Meta):
                fields = (
                    *cls.Meta.fields,
                    controller_field_name,
                    controlled_field_name,
                )

        return ModelFormMetaclass(
            f"ControlledDatalistFormFor{cls.__name__}",
            (cls,),
            {
                "Meta": Meta,
                "clean": clean,
                controlled_field_name: MultiDatalistIntegerField(
                    widget=ControlledDatalistsWidget(
                        controller_field_name=controller_field_name,
                        controlled_field_name=controlled_field_name,
                        widgets={
                            controller_value: Datalist(
                                choices=controlled_choices,
                            )
                            for controller_value, controlled_choices in choices.items()
                        },
                    ),
                ),
            },
        )

    return wrap_in_subclass
