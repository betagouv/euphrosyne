from datetime import time
from typing import Any, Optional, Tuple

from django import forms
from django.contrib.admin import site
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.widgets import AdminSplitDateTime, RelatedFieldWidgetWrapper
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

from euphro_auth.models import User
from lab.models.run import Run


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


class LeaderReadonlyWidget(Widget):
    template_name = "widgets/leader_readonly.html"

    class Media:
        js = ("js/admin/ViewObjectLookups.js",)

    def __init__(self, project_id: int, user: User = None, attrs=None):
        self.user = user
        self.project_id = project_id
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        return {
            **context,
            "user": self.user,
            "project_id": self.project_id,
        }


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


class TagsInput(Input):
    template_name = "widgets/tags_input.html"

    class Media:
        js = ("js/widgets/tags-input.js",)
        css = {"all": ("css/widgets/tags-input.css",)}


class SplitDateTimeWithDefaultTime(AdminSplitDateTime):
    def __init__(
        self,
        attrs: Optional[dict[str, str]] = None,
        default_time_value: time = None,
    ) -> None:
        self.default_time_value = default_time_value
        super().__init__(attrs)

    def get_context(
        self, name: str, value: Any, attrs: Optional[dict[str, str]]
    ) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        if (
            not context["widget"]["value"]
            and not context["widget"]["subwidgets"][1]["value"]
        ):
            context["widget"]["subwidgets"][1]["value"] = self.default_time_value
        return context


class CounterTextarea(Textarea):
    template_name = "widgets/counter_textarea.html"

    class Media:
        js = ("js/widgets/counter-textarea.js",)


class PlaceholderSelect(Select):
    template_name = "widgets/placeholder_select.html"


class ChoiceTag(ChoiceWidget):
    template_name = "widgets/choice_tag.html"

    class Media:
        js = ("js/widgets/choice-tag.js",)


class RelatedObjectRunWidgetWrapper(RelatedFieldWidgetWrapper):
    template_name = "widgets/related_object_run_widget_wrapper.html"

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        run: Run,
        admin_site: AdminSite,
        can_add_related=None,
        can_change_related=False,
        can_delete_related=False,
        can_view_related=False,
    ) -> None:
        self.run = run
        super().__init__(
            PlaceholderSelect(),
            # pylint: disable=no-member
            Run.run_object_groups.rel,
            admin_site,
            can_add_related,
            can_change_related,
            can_delete_related,
            can_view_related,
        )

    def get_context(
        self, name: str, value: Any, attrs: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        context["url_params"] += f"&run={self.run.id}"
        return {
            **context,
        }
