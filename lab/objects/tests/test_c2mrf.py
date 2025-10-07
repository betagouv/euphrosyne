from unittest import mock

from ..models import Era, ObjectGroup
from ..providers import (
    construct_image_url,
    fetch_full_objectgroup,
    fetch_partial_objectgroup,
)

EROS_RESPONSE = {
    "ctechnique": "majolique lustrée",
    "dtfrom": "1500",
    "dtto": "1600",
    "inv": "ODUT 01107",
    "local": "France, Paris, musée du Petit Palais",
    "owner": "France, Paris, ville",
    "support": "terre cuite",
    "technique": "glaçure",
    "title": "Majolique",
    "worknbr": "C2RMF65980",
}


@mock.patch(
    "lab.objects.providers.c2rmf.C2RMFProvider._fetch_raw_data",
    return_value=EROS_RESPONSE,
)
def test_fetch_partial_objectgroup_from_c2rmf(_):
    assert fetch_partial_objectgroup("c2rmf", "C2RMF65980") == {
        "c2rmf_id": "C2RMF65980",
        "label": "Majolique",
    }


@mock.patch(
    "lab.objects.providers.c2rmf.C2RMFProvider._fetch_raw_data",
    return_value=EROS_RESPONSE,
)
def test_fetch_full_objectgroup_from_c2rmf(_):
    og = fetch_full_objectgroup("c2rmf", "C2RMF65980")
    assert isinstance(og, ObjectGroup)
    assert og.object_count == 1
    assert og.c2rmf_id == "C2RMF65980"
    assert og.label == "Majolique"
    assert isinstance(og.dating_era, Era)
    assert og.dating_era.label == "1500"
    assert og.inventory == "ODUT 01107"
    assert og.materials == ["terre cuite"]


@mock.patch("lab.objects.providers.c2rmf.settings")
def test_construct_image_url_from_c2rmf_path(mock_settings):

    mock_settings.EROS_BASE_IMAGE_URL = "http://example.com"
    mock_settings.EUPHROSYNE_TOOLS_API_URL = "http://tools.example.com"

    path = "C2RMF12345/67890"
    expected_url = "http://example.com/iiif/pyr-C2RMF1/C2RMF12345/67890.tif/full/500,/0/default.jpg?token="  # pylint: disable=line-too-long
    assert construct_image_url("c2rmf", path).startswith(expected_url)

    path = "F12345/67890"
    expected_url = (
        "http://example.com/iiif/pyr-F1/F12345/67890.tif/full/500,/0/default.jpg?token="
    )
    assert construct_image_url("c2rmf", path).startswith(expected_url)

    path = "Z12345/67890"
    expected_url = (
        "http://example.com/iiif/pyr-FZ/Z12345/67890.tif/full/500,/0/default.jpg?token="
    )
    assert construct_image_url("c2rmf", path).startswith(expected_url)

    # Euphro tools token when EROS_BASE_IMAGE_URL is None
    mock_settings.EROS_BASE_IMAGE_URL = None
    path = "C2RMF12345/67890"
    expected_url = "http://tools.example.com/eros/iiif/pyr-C2RMF1/C2RMF12345/67890.tif/full/500,/0/default.jpg?token="  # pylint: disable=line-too-long
    assert construct_image_url("c2rmf", path).startswith(expected_url)
