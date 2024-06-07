from unittest import mock

from ..opentheso import fetch_parent_ids_from_id


@mock.patch("lab.opentheso.requests")
def test_fetch_parent_ids_from_id(request_mock: mock.MagicMock):
    response_data = {
        "ELEMENT/IGNORED_ELEMENT": {},
        "ELEMENT/FIRST": {},
        "ELEMENT/BLABLA/SECOND": {},
    }
    request_mock.get.return_value.json.return_value = response_data

    assert fetch_parent_ids_from_id("theso_id", "concept_id") == ["FIRST", "SECOND"]
    request_mock.get.assert_called_once_with(
        # pylint: disable=line-too-long
        "https://opentheso.huma-num.fr/opentheso/openapi/v1/concept/theso_id/concept_id/expansion?way=top",
        timeout=5,
    )
