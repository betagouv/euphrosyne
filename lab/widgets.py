from typing import Any, Dict, Optional, Sequence, Tuple, Type, Union

from django import forms
from django.conf import settings
from django.contrib.admin import site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.forms.renderers import get_default_renderer
from django.forms.widgets import HiddenInput, MultiWidget, Select, Widget
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


class ProjectWidgetWrapper(RelatedFieldWidgetWrapper):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        widget: forms.Widget,
        rel: ForeignObjectRel,
        can_add_related: Optional[bool] = None,
        can_change_related: bool = None,
        can_delete_related: bool = None,
        can_view_related: bool = None,
    ) -> None:
        super().__init__(
            widget,
            rel,
            site,
            # [FIXME] Add button still working
            can_add_related=False,
            can_change_related=False,
            can_delete_related=False,
            can_view_related=False,
        )


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
    control_value: str

    def _build_controlled_datalist_label(self, control_value: str):
        return f"{self.field_name}__{control_value}"

    def __init__(
        self,
        field_name: str,
        control_value: str,
        choices: Sequence[Tuple[Any, Any]] = None,
        attrs: Optional[Any] = None,
    ):
        self.field_name = field_name
        self.control_value = control_value
        super().__init__(
            choices=choices,
            attrs={
                "controlled-datalist-label": self._build_controlled_datalist_label(
                    control_value
                ),
                **(attrs if attrs else {}),
            },
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"][
            "controlled_datalist_label_prefix"
        ] = self._build_controlled_datalist_label("")
        return context


class MultiDatalistWidget(MultiWidget):
    """Show the datalist widget corresponding to a given form input value"""

    control_field_name: str

    class Media:
        # See django/contrib/admin/widgets.py:AutocompleteMixin
        # [TODO] Add raincoat comment
        extra = "" if settings.DEBUG else ".min"
        js = (
            "admin/js/vendor/jquery/jquery%s.js" % extra,
            "admin/js/vendor/select2/select2.full%s.js" % extra,
            "admin/js/jquery.init.js",
        )

    def __init__(
        self,
        control_field_name: str,
        widgets: Sequence[Union[Widget, Type[Widget]]],
        attrs: Optional[Any] = None,
    ) -> None:
        super().__init__(widgets, attrs)
        self.control_field_name = control_field_name

    def get_context(
        self, name: str, value: Any, attrs: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "control_field_name": self.control_field_name,
            **super().get_context(name, value, attrs),
        }

    def decompress(self, value: Any) -> Optional[Any]:
        return [value] * len(self.widgets)
