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


class ControlledDatalist(Datalist):
    field_name: str
    controller_value: str
    template_name = "forms/widgets/controlled_datalist.html"

    def __init__(
        self,
        field_name: str,
        controller_value: str,
        choices: Sequence[Tuple[Any, Any]] = None,
        attrs: Optional[Any] = None,
    ):
        self.field_name = field_name
        self.controller_value = controller_value
        super().__init__(choices=choices, attrs=attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["controlled_name_prefix"] = f"{self.field_name}_"
        return context


class MultiDatalistWidget(MultiWidget):
    """Show the datalist widget corresponding to a given form input value"""

    controller_field_name: str

    def __init__(
        self,
        controller_field_name: str,
        widgets: Sequence[Union[Widget, Type[Widget]]],
        attrs: Optional[Any] = None,
    ) -> None:
        super().__init__(widgets, attrs)
        self.controller_field_name = controller_field_name

    def get_context(
        self, name: str, value: Any, attrs: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "controller_field_name": self.controller_field_name,
            **super().get_context(name, value, attrs),
        }

    def decompress(self, value: Any) -> Optional[Any]:
        return [value] * len(self.widgets)


class MultiDatalistIntegerField(IntegerField):
    widget = MultiDatalistWidget

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
    def wrap_in_subclass(cls):
        def clean(self):  # pylint: disable=unused-argument
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

        class Meta(cls.Meta):
            fields = tuple(cls.Meta.fields) + (
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
                    widget=MultiDatalistWidget(
                        controller_field_name=controller_field_name,
                        widgets={
                            controller_value: ControlledDatalist(
                                field_name=controlled_field_name,
                                controller_value=controller_value,
                                choices=controlled_choices,
                            )
                            for controller_value, controlled_choices in choices.items()
                        },
                    ),
                ),
            },
        )

    return wrap_in_subclass
