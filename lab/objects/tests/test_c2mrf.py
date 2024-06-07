from unittest import mock

from ..c2rmf import (
    fetch_full_objectgroup_from_eros,
    fetch_partial_objectgroup_from_eros,
)
from ..models import Era, ObjectGroup

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
    "lab.objects.c2rmf._fetch_object_group_from_eros", return_value=EROS_RESPONSE
)
def test_fetch_partial_objectgroup_from_eros(_):
    assert fetch_partial_objectgroup_from_eros("C2RMF65980") == {
        "c2rmf_id": "C2RMF65980",
        "label": "Majolique",
    }


@mock.patch(
    "lab.objects.c2rmf._fetch_object_group_from_eros", return_value=EROS_RESPONSE
)
def test_fetch_full_objectgroup_from_eros(_):
    og = fetch_full_objectgroup_from_eros("C2RMF65980")
    assert isinstance(og, ObjectGroup)
    assert og.object_count == 1
    assert og.c2rmf_id == "C2RMF65980"
    assert og.label == "Majolique"
    assert isinstance(og.dating_era, Era)
    assert og.dating_era.label == "1500"
    assert og.inventory == "ODUT 01107"
    assert og.materials == ["terre cuite"]
