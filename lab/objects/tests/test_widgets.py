from .. import widgets


def test_importfrominput_widget():
    widget = widgets.ImportFromInput("https://url", {"label": "label-id"})
    context = widget.get_context("label", "hello", None)

    assert widget.field_id_mapping == {"label": "label-id"}
    assert context["widget"]["field_id_mapping"] == (("label", "label-id"),)
    assert context["widget"]["attrs"]["import_url_name"] == "https://url"
