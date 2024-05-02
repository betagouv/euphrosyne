from typing import Optional

from django import forms
from django.contrib.admin import site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.fields.reverse_related import ForeignObjectRel

from lab.models import Institution
from lab.widgets import AutoCompleteWidget


class InstitutionAutoCompleteWidget(AutoCompleteWidget):
    template_name = "widgets/institution_autocomplete_widget.html"

    model = Institution

    class Media:
        js = (
            "web-components/institution-type-ahead.js",
            "js/widgets/institution-autocomplete-widget.js",
        )
        css = {"all": ("css/widgets/autocomplete-widget.css",)}


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
