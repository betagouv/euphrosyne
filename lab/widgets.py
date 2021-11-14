from typing import Any, Optional, Tuple

from django import forms
from django.contrib.admin import site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.forms.renderers import get_default_renderer
from django.forms.widgets import HiddenInput, Select, Widget
from django.urls import reverse
from django.utils.safestring import mark_safe


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


class LeaderReadonlyWidget:
    template_name = "widgets/leader_readonly.html"

    def render(self, context, renderer=None):
        renderer = get_default_renderer()
        return mark_safe(renderer.render(self.template_name, context))


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
