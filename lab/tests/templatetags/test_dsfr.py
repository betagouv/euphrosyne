from lab.templatetags import dsfr as dsfr_tags


def test_attrs_with_dsfr():
    context = {"widget": {"attrs": {"class": "form-control"}}}
    result = dsfr_tags.attrs_with_dsfr(context)
    assert result == {"widget": {"attrs": {"class": "form-control fr-input"}}}
