from typing import Any, Dict

from django.conf import settings
from django.forms import widgets

from lab.thesauri.models import ThesorusConceptModel
from lab.widgets import AutoCompleteWidget

from .models import Era, Location, Period


class ImportFromInput(widgets.TextInput):
    """Text input that does AJAX request to fetch information and fill up related
    fields from a model form."""

    input_type = "text"
    template_name = "widgets/import_from_input.html"

    class Media:
        js = ("js/widgets/import-from-input.js",)

    def __init__(
        self,
        import_url: str,
        field_id_mapping: dict[str, str],
        attrs: dict | None = None,
    ):
        """
        Parameters
        ----------
        import_url :
            URL to use for fetching data. Must be a valid Django URL name.
        field_id_mapping :
            Dict where keys are the property names from the response and values the
            related HTML ID of the elements to complete in the form after fetching
            data from `import_url`.
            Example: { "label": "label-id" }
        """
        self.field_id_mapping = field_id_mapping
        super().__init__(
            {
                **(attrs or {}),
                "import_url": import_url,
            }
        )

    def get_context(self, name: str, value: Any, attrs: dict | None) -> Dict[str, Any]:
        context = super().get_context(name, value, attrs)
        context["facility_name"] = settings.FACILITY_NAME
        context["widget"]["field_id_mapping"] = tuple(
            (
                key,
                field,
            )
            for key, field in self.field_id_mapping.items()
        )
        return context


class LocationAutoCompleteWidget(AutoCompleteWidget):
    template_name = "widgets/location_autocomplete_widget.html"

    model = Location

    class Media:
        js = (
            "web-components/location-type-ahead.js",
            "js/widgets/location-autocomplete-widget.js",
        )
        css = {"all": ("css/widgets/autocomplete-widget.css",)}


class DatingAutoCompleteWidget(AutoCompleteWidget):
    model: type[ThesorusConceptModel] | None = None

    template_name = "widgets/dating_autocomplete_widget.html"

    def get_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None
    ) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        if self.model is None:
            raise ValueError("model is required")
        context["widget"]["field_name"] = self.model.__name__.lower()
        # pylint: disable=no-member
        context["widget"]["opentheso_theso_id"] = self.model.OPENTHESO_THESO_ID
        return context


class PeriodDatingAutoCompleteWidget(DatingAutoCompleteWidget):
    model = Period
    typeahead_list_webcomponent_name = "period-type-ahead"

    class Media:
        js = (
            "web-components/dating-open-theso-type-ahead.js",
            "js/widgets/dating-autocomplete-widget.js",
        )
        css = {"all": ("css/widgets/autocomplete-widget.css",)}


class EraDatingAutoCompleteWidget(DatingAutoCompleteWidget):
    model = Era
    typeahead_list_webcomponent_name = "era-type-ahead"

    class Media:
        js = (
            "web-components/dating-open-theso-type-ahead.js",
            "js/widgets/dating-autocomplete-widget.js",
        )
        css = {"all": ("css/widgets/autocomplete-widget.css",)}
