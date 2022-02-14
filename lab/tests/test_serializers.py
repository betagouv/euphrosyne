import datetime
from unittest import mock

from django.test.client import RequestFactory

from ..serializers import convert_for_ui


def test_convert_for_ui_datetime():
    request = RequestFactory().post("/")
    request.LANGUAGE_CODE = "en-US"
    obj = mock.Mock(
        start_date=datetime.datetime(2022, 1, 1, 0, 0),
    )
    english_serialization = convert_for_ui(request, obj, ["start_date"])

    assert english_serialization == {
        "start_date": "01 January 2022 00:00",
    }
