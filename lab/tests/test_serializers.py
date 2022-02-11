import datetime

from django.test.client import RequestFactory
from django.urls import reverse

from ..models import Run
from ..serializers import convert_for_ui


def test_convert_for_ui_datetime():
    request = RequestFactory().post(
        reverse("admin:lab_run_add"),
    )
    request.LANGUAGE_CODE = "en-US"
    run = Run(
        id=42,
        label="42label",
        start_date=datetime.datetime(2022, 1, 1, 0, 0),
    )
    english_serialization = convert_for_ui(request, run, ["start_date"])

    assert english_serialization == {
        "start_date": "01 January 2022 00:00",
    }
