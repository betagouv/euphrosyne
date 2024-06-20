from typing import Any, Optional, Type

from django import forms
from django.db import models
from django.forms.widgets import (
    ChoiceWidget,
    HiddenInput,
    Input,
    Select,
    Textarea,
    Widget,
)


class AutoCompleteWidget(Widget):
    template_name = ""

    model: Type[models.Model] | None = None
    instance: models.Model | None = None

    def get_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None
    ) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        if self.instance:
            context["widget"]["instance"] = self.instance
        elif value:
            if self.model is None:
                raise ValueError("model is required")
            # pylint: disable=protected-access
            context["widget"]["instance"] = self.model._default_manager.get(pk=value)
        else:
            context["widget"]["instance"] = None
        return context


class DisabledSelectWithHidden(Select):
    hidden_widget: HiddenInput

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs_disabled = {**attrs, **{"disabled": "disabled"}}
        attrs_not_disabled = {k: v for k, v in attrs.items() if k != "disabled"}
        self.hidden_widget = HiddenInput(attrs_not_disabled)
        super().__init__(attrs_disabled)

    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, value, attrs, renderer) + self.hidden_widget.render(
            name, value, attrs, renderer
        )

    def value_from_datadict(self, data, files, name):
        return self.hidden_widget.value_from_datadict(data, files, name)


class TagsInput(Input):
    template_name = "widgets/tags_input.html"

    class Media:
        js = (
            "web-components/material-type-ahead.js",
            "js/widgets/tags-input.js",
        )
        css = {"all": ("css/widgets/tags-input.css",)}


class SplitDateTimeWithDefaultTime(forms.SplitDateTimeWidget):
    template_name = "admin/lab/widgets/split_datetime.html"

    def __init__(
        self,
        default_time_value=None,
        attrs=None,
    ):
        self.default_time_value = default_time_value
        super().__init__(
            attrs,
            "%Y-%m-%d",
        )

    def get_context(
        self, name: str, value: Any, attrs: Optional[dict[str, str]]
    ) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        if (
            not context["widget"]["value"]
            and not context["widget"]["subwidgets"][1]["value"]
        ):
            context["widget"]["subwidgets"][1]["value"] = self.default_time_value
        context["widget"]["subwidgets"][0]["type"] = "date"
        context["widget"]["subwidgets"][1]["type"] = "time"
        return context


class CounterTextarea(Textarea):
    template_name = "widgets/counter_textarea.html"

    class Media:
        js = ("js/widgets/counter-textarea.js",)


class ChoiceTag(ChoiceWidget):
    template_name = "widgets/choice_tag.html"

    class Media:
        js = ("js/widgets/choice-tag.js",)
