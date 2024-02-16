from lab.templatetags import dsfr as dsfr_tags


def test_attrs_with_dsfr_for_any_field():
    context = {
        "widget": {"template_name": "any.html", "attrs": {"class": "form-control"}}
    }
    result = dsfr_tags.attrs_with_dsfr(context)
    assert result == {
        "widget": {
            "template_name": "any.html",
            "attrs": {"class": "form-control fr-input"},
        }
    }


def test_attrs_with_dsfr_for_select_field():
    context = {
        "widget": {"template_name": "select.html", "attrs": {"class": "form-control"}}
    }
    result = dsfr_tags.attrs_with_dsfr(context)
    assert result == {
        "widget": {
            "template_name": "select.html",
            "attrs": {"class": "form-control fr-select"},
        }
    }


def test_label_tag_with_dsfr():
    assert (
        dsfr_tags.label_tag_with_dsfr("<label>Test</label>")
        == '<label class="fr-label">Test</label>'
    )
