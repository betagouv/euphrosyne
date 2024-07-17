import pytest
from django.test import RequestFactory

from euphro_auth.tests import factories as auth_factories

from ..nav import get_nav_items


@pytest.mark.django_db
def test_get_nav_items_for_admin():
    request = RequestFactory().get("/")
    request.user = auth_factories.LabAdminUserFactory()
    assert get_nav_items(request) == [
        {
            "title": "Tableau de bord",
            "href": "/",
            "iconName": "fr-icon-calendar-line",
            "exactPath": True,
            "extraPath": [],
        },
        {
            "title": "Projets",
            "href": "/lab/project/",
            "iconName": "fr-icon-survey-line",
            "extraPath": ["/lab/run/"],
            "exactPath": False,
        },
        {
            "title": "Utilisateurs",
            "href": "/euphro_auth/user/",
            "iconName": "fr-icon-user-line",
            "exactPath": False,
            "extraPath": ["/euphro_auth/userinvitation/"],
        },
        {
            "title": "Demandes de données",
            "href": "/data_request/datarequest/",
            "iconName": "fr-icon-download-line",
            "exactPath": False,
            "extraPath": None,
            "badge": 0,
        },
    ]


@pytest.mark.django_db
def test_get_nav_items_for_staff():
    request = RequestFactory().get("/")
    request.user = auth_factories.StaffUserFactory()
    assert get_nav_items(request) == [
        {
            "title": "Projets",
            "href": "/lab/project/",
            "iconName": "fr-icon-survey-line",
            "extraPath": ["/lab/run/"],
            "exactPath": False,
        },
        {
            "title": "Compte",
            "href": f"/euphro_auth/user/{request.user.id}/change/",
            "iconName": "fr-icon-user-line",
            "exactPath": False,
            "extraPath": [],
        },
    ]
