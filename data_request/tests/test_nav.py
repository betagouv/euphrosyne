import pytest
from django.test import RequestFactory
from django.utils.translation import gettext

from euphro_auth.tests import factories as auth_factories

from ..nav import get_nav_items
from . import factories


@pytest.mark.django_db
def test_data_request_nav():
    request = RequestFactory()
    request.user = auth_factories.StaffUserFactory()

    # pylint: disable=use-implicit-booleaness-not-comparison
    assert get_nav_items(request) == []

    request.user = auth_factories.LabAdminUserFactory()
    factories.DataRequestFactory(request_viewed=False)
    assert get_nav_items(request) == [
        {
            "title": gettext("Data requests"),
            "item": {
                "href": "/data_request/datarequest/",
                "iconName": "fr-icon-download-line",
                "exactPath": False,
                "extraPath": None,
                "badge": 1,
            },
        }
    ]
