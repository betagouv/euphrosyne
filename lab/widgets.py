from typing import Any, Optional, Tuple

from django import forms
from django.contrib.admin import site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.urls import reverse


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
