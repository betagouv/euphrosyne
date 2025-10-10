from unittest import mock

import pytest
from django.forms import ValidationError

from lab.tests import factories

from ...forms import ObjectGroupImportErosForm
from ...providers import ObjectProviderError


def test_form_conf():
    form = ObjectGroupImportErosForm()
    assert set(form.fields.keys()) == {"provider_object_id", "label"}
    assert form.fields["label"].disabled
    assert not form.fields["label"].required


@pytest.mark.django_db
@mock.patch("lab.objects.forms.fetch_partial_objectgroup")
def test_clean_fetch_data(mock_fetch: mock.MagicMock):
    mock_fetch.return_value = {
        "label": "Test",
    }
    form = ObjectGroupImportErosForm()
    form.cleaned_data = {"provider_object_id": "C2RMF00000"}
    cleaned_data = form.clean()

    mock_fetch.assert_called_once_with("eros", "C2RMF00000")
    assert "object_group" in cleaned_data
    assert cleaned_data["object_group"]["label"] == "Test"


@pytest.mark.django_db
@mock.patch("lab.objects.forms.fetch_partial_objectgroup")
def test_clean_raises_if_fetch_none(mock_fetch: mock.MagicMock):
    mock_fetch.return_value = None
    form = ObjectGroupImportErosForm()
    form.cleaned_data = {"provider_object_id": "C2RMF00000"}
    with pytest.raises(ValidationError):
        form.clean()


@pytest.mark.django_db
@mock.patch("lab.objects.forms.fetch_partial_objectgroup")
def test_clean_raises_if_fetch_fails(mock_fetch: mock.MagicMock):
    mock_fetch.side_effect = ObjectProviderError()
    form = ObjectGroupImportErosForm()
    form.cleaned_data = {"provider_object_id": "C2RMF00000"}
    with pytest.raises(ValidationError):
        form.clean()


@pytest.mark.django_db
def test_clean_set_form_if_obj_exists():
    eros_id = "C2RMF00000"
    objectgroup = factories.ExternalObjectReferenceFactory(
        provider_name="eros", provider_object_id=eros_id
    )

    form = ObjectGroupImportErosForm()
    form.cleaned_data = {"provider_object_id": eros_id}
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
    form = ObjectGroupImportErosForm(data={"provider_object_id": "c2rmf00000"})
    form.full_clean()

    assert form.cleaned_data["provider_object_id"] == "C2RMF00000"
