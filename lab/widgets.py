from typing import Any, Optional, Tuple

from django import forms
from django.contrib.admin import site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.forms.widgets import (
    ChoiceWidget,
    HiddenInput,
    Input,
    Select,
    Textarea,
    Widget,
)
from django.urls import reverse

from lab.models.participation import Institution


class UserWidgetWrapper(RelatedFieldWidgetWrapper):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        widget: forms.Widget,
        rel: ForeignObjectRel,
        can_add_related: Optional[bool] = ...,
        can_change_related: bool = ...,
        can_delete_related: bool = ...,
        can_view_related: bool = ...,
    ) -> None:
        super().__init__(
            widget,
            rel,
            site,
            can_add_related=can_add_related,
            can_change_related=False,
            can_delete_related=False,
            can_view_related=can_view_related,
        )

    def get_related_url(self, info: Tuple[str, str], action: str, *args: Any) -> str:
        if action == "add":
            return reverse("admin:euphro_auth_userinvitation_add")
        return super().get_related_url(info, action, *args)


class InstitutionAutoCompleteWidget(Widget):
    input_type = "text"
    template_name = "widgets/institution_autocomplete_widget.html"

    instance: Institution | None = None

    def get_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None
    ) -> dict[str, Any]:
        attrs = attrs or {}
        attrs["class"] = "fr-input"
        context = super().get_context(name, value, attrs)
        if self.instance:
            context["widget"]["instance"] = self.instance
        elif value:
            context["widget"]["instance"] = Institution.objects.get(pk=value)
        else:
            context["widget"]["instance"] = None
        return context

    class Media:
        js = (
            "web-components/institution-type-ahead.js",
            "js/widgets/institution-autocomplete-widget.js",
        )
        css = {"all": ("css/widgets/institution-autocomplete-widget.css",)}


class InstitutionWidgetWrapper(RelatedFieldWidgetWrapper):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        widget: forms.Widget,
        rel: ForeignObjectRel,
        can_add_related: Optional[bool] = ...,
        can_change_related: bool = ...,
        can_delete_related: bool = ...,
        can_view_related: bool = ...,
    ) -> None:
        super().__init__(
            widget,
            rel,
            site,
            can_add_related=can_add_related,
            can_change_related=False,
            can_delete_related=False,
            can_view_related=can_view_related,
        )


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
        js = ("js/widgets/tags-input.js",)
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
