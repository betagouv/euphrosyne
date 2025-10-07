from unittest import mock

import pytest
from django.forms import ValidationError

from lab.tests import factories

from ...forms import ObjectGroupImportC2RMFForm
from ...providers import ObjectProviderError


def test_form_conf():
    form = ObjectGroupImportC2RMFForm()
    assert set(form.fields.keys()) == {"c2rmf_id", "label", "object_count"}
    assert form.fields["object_count"].initial == 1
    assert form.fields["label"].disabled
    assert not form.fields["label"].required


@pytest.mark.django_db
@mock.patch("lab.objects.forms.fetch_partial_objectgroup")
def test_clean_fetch_data(mock_fetch: mock.MagicMock):
    mock_fetch.return_value = {
        "worknbr": "C2RMF00000",
        "label": "Test",
    }
    form = ObjectGroupImportC2RMFForm()
    form.cleaned_data = {"c2rmf_id": "C2RMF00000"}
    cleaned_data = form.clean()

    mock_fetch.assert_called_once_with("c2rmf", "C2RMF00000")
    assert cleaned_data["label"] == "Test"
    assert cleaned_data["object_count"] == 1


@pytest.mark.django_db
@mock.patch("lab.objects.forms.fetch_partial_objectgroup")
def test_clean_raises_if_fetch_none(mock_fetch: mock.MagicMock):
    mock_fetch.return_value = None
    form = ObjectGroupImportC2RMFForm()
    form.cleaned_data = {"c2rmf_id": "C2RMF00000"}
    with pytest.raises(ValidationError):
        form.clean()


@pytest.mark.django_db
@mock.patch("lab.objects.forms.fetch_partial_objectgroup")
def test_clean_raises_if_fetch_fails(mock_fetch: mock.MagicMock):
    mock_fetch.side_effect = ObjectProviderError()
    form = ObjectGroupImportC2RMFForm()
    form.cleaned_data = {"c2rmf_id": "C2RMF00000"}
    with pytest.raises(ValidationError):
        form.clean()


@pytest.mark.django_db
def test_clean_set_form_if_obj_exists():
    c2rmf_id = "C2RMF00000"
    objectgroup = factories.ObjectGroupFactory(c2rmf_id=c2rmf_id)

    form = ObjectGroupImportC2RMFForm()
    form.cleaned_data = {"c2rmf_id": c2rmf_id}
    form.clean()

    assert form.instance
    assert form.instance.id == objectgroup.id


@pytest.mark.django_db
@mock.patch("lab.objects.forms.fetch_partial_objectgroup")
def test_clean_c2rmf_id_upper(mock_fetch: mock.MagicMock):
    mock_fetch.return_value = {
        "worknbr": "C2RMF00000",
        "label": "Test",
    }
    form = ObjectGroupImportC2RMFForm(data={"c2rmf_id": "c2rmf00000"})
    form.full_clean()

    assert form.cleaned_data["c2rmf_id"] == "C2RMF00000"
