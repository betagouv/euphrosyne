import typing

from django import forms
from django.contrib.admin import site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.fields.reverse_related import ManyToOneRel

from lab.models import Institution
from lab.widgets import AutoCompleteWidget

if typing.TYPE_CHECKING:
    from django.forms.widgets import ChoiceWidget


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
        widget: "ChoiceWidget",
        rel: ManyToOneRel,
        can_add_related: bool | None = None,
        can_change_related: bool = False,
        can_delete_related: bool = False,
        can_view_related: bool = False,
    ):
        super().__init__(
            widget,
            rel,
            site,
            can_add_related=can_add_related,
            can_change_related=False,
            can_delete_related=False,
            can_view_related=can_view_related,
        )


class ParticipationCertificationWidget(forms.Widget):
    template_name = "widgets/participation_certification_widget.html"

    class Media:
        css = {"all": ("css/widgets/participation-certification-widget.css",)}
