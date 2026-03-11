from unittest import mock

from ...models import Era, ObjectGroup, Period
from ...providers import (
    construct_image_url,
    fetch_full_objectgroup,
    fetch_object_image_urls,
    fetch_partial_objectgroup,
)
from ...providers.pop import POP_BASE_URL, POPProvider

POP_RESPONSE = {
    "Reference": "50010009167",
    "Titre": "Les deux rennes se suivant",
    "Denomination": "rhombe;navette",
    "Periode_de_creation": "1er siècle av JC;1er siècle",
    "Epoque": "Magdalénien supérieur",
    "Numero_inventaire": "83367",
    "Materiaux_techniques": "bois de cervidé;incision",
    "Lien_site_associe": "https://example.com/image1.jpg;https://example.com/image2.jpg",
    "Source_de_la_representation": "https://example.com/image1.jpg",
}


@mock.patch(
    "lab.objects.providers.pop.POPProvider._fetch_raw_data",
    return_value={**POP_RESPONSE, "Titre": None},
)
def test_fetch_partial_objectgroup_from_pop(mock_fetch_raw_data):
    assert fetch_partial_objectgroup("pop", "50010009167") == {
        "label": "rhombe;navette",
    }
    mock_fetch_raw_data.assert_called_once_with("50010009167")


@mock.patch(
    "lab.objects.providers.pop.POPProvider._fetch_raw_data",
    return_value=POP_RESPONSE,
)
def test_fetch_full_objectgroup_from_pop(_):
    og = fetch_full_objectgroup("pop", "50010009167")
    assert isinstance(og, ObjectGroup)
    assert og.object_count == 1
    assert og.label == "Les deux rennes se suivant"
    assert isinstance(og.dating_period, Period)
    assert og.dating_period.label == "1er siècle av JC, 1er siècle"
    assert isinstance(og.dating_era, Era)
    assert og.dating_era.label == "Magdalénien supérieur"
    assert og.inventory == "83367"
    assert og.materials == ["bois de cervidé", "incision"]


@mock.patch(
    "lab.objects.providers.pop.POPProvider._fetch_raw_data",
    return_value=POP_RESPONSE,
)
def test_fetch_object_image_urls_from_pop(_):
    assert fetch_object_image_urls("pop", "50010009167") == [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
    ]


def test_construct_image_url_from_pop_path():
    assert (
        construct_image_url("pop", "joconde/12345.webp")
        == "https://pop-perf-assets.s3.gra.io.cloud.ovh.net/joconde/12345.webp"
    )
    assert (
        construct_image_url("pop", "/joconde/12345.webp")
        == "https://pop-perf-assets.s3.gra.io.cloud.ovh.net/joconde/12345.webp"
    )


@mock.patch("lab.objects.providers.pop.requests.get")
def test_pop_provider_fetch_raw_data_uses_tabular_api(mock_get):
    response = mock.Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"data": [{"Reference": "50010009167"}]}
    mock_get.return_value = response

    provider = POPProvider()
    assert provider._fetch_raw_data("50010009167") == {"Reference": "50010009167"}
    mock_get.assert_called_once_with(
        POP_BASE_URL,
        params={"Reference__exact": "50010009167", "page_size": 1},
        timeout=5,
    )
