from typing import Any, Dict

from django.forms import widgets


class ImportFromInput(widgets.TextInput):
    """Text input that does AJAX request to fetch information and fill up related
    fields from a model form."""

    input_type = "text"
    template_name = "widgets/import_from_input.html"

    class Media:
        js = ("js/widgets/import-from-input.js",)

    def __init__(
        self,
        import_url_name: str,
        field_id_mapping: dict[str, str],
        attrs: dict | None = None,
    ):
        """
        Parameters
        ----------
        import_url_name :
            Name of the URL to use for fetching data. Must be a valid Django URL name.
        field_id_mapping :
            Dict where keys are the property names from the response and values the
            related HTML ID of the elements to complete in the form after fetching
            data from `import_url_name`.
            Example: { "label": "label-id" }
        """
        self.field_id_mapping = field_id_mapping
        super().__init__(
            {
                **(attrs or {}),
                "import_url_name": import_url_name,
            }
        )

    def get_context(self, name: str, value: Any, attrs: dict | None) -> Dict[str, Any]:
        context = super().get_context(name, value, attrs)
        context["widget"]["field_id_mapping"] = tuple(
            (
                key,
                field,
            )
            for key, field in self.field_id_mapping.items()
        )
        return context
