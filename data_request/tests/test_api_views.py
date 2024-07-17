from unittest import mock

import pytest
from rest_framework import serializers

from lab.tests import factories

from ..api_views import DataRequestCreateAPIView, DataRequestSerializer


@pytest.mark.django_db
def test_data_request_create_api_view_send_mail():
    data = DataRequestSerializer(
        None,
        {
            "user_email": "dev@euphrosyne.fr",
            "user_first_name": "Dev",
            "user_last_name": "euphrosyne",
            "user_institution": "euphrosyne Institute of Technology",
            "description": "I need this data for my research.",
            "runs": [factories.NotEmbargoedRun().id],
        },
    )
    data.is_valid(raise_exception=True)

    with mock.patch(
        "data_request.api_views.send_data_request_created_email"
    ) as send_mail_mock:
        DataRequestCreateAPIView().perform_create(serializer=data)
        send_mail_mock.assert_called_with("dev@euphrosyne.fr")


@pytest.mark.django_db
def test_data_request_create_api_view_when_embargoed_run():
    data = DataRequestSerializer(
        None,
        {
            "user_email": "dev@euphrosyne.fr",
            "user_first_name": "Dev",
            "user_last_name": "euphrosyne",
            "user_institution": "euphrosyne Institute of Technology",
            "description": "I need this data for my research.",
            "runs": [factories.RunFactory().id],
        },
    )
    with pytest.raises(serializers.ValidationError):
        data.is_valid(raise_exception=True)
