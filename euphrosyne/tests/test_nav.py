import pytest
from django.test import RequestFactory

from euphro_auth.tests import factories as auth_factories

from ..nav import get_nav_items


@pytest.mark.django_db
def test_get_nav_items_for_admin():
    request = RequestFactory().get("/")
    request.user = auth_factories.LabAdminUserFactory()
    print(get_nav_items(request))
    assert get_nav_items(request) == [
        {
            "title": "Tableau de bord",
            "item": {
                "href": "/",
                "iconName": "fr-icon-calendar-line",
                "exactPath": True,
                "extraPath": [],
            },
        },
        {
            "title": "Projets",
            "item": {
                "href": "/lab/project/",
                "iconName": "fr-icon-survey-line",
                "extraPath": ["/lab/run/"],
                "exactPath": False,
            },
        },
        {
            "title": "Utilisateurs",
            "item": {
                "href": "/euphro_auth/user/",
                "iconName": "fr-icon-user-line",
                "exactPath": False,
                "extraPath": ["/euphro_auth/userinvitation/"],
            },
        },
        {
            "title": "Demandes de données",
            "item": {
                "href": "/data_request/datarequest/",
                "iconName": "fr-icon-download-line",
                "exactPath": False,
                "extraPath": None,
                "badge": 0,
            },
        },
        {
            "title": "Administration",
            "items": [
                {
                    "title": "Certifications",
                    "item": {
                        "href": "/certification/certification/",
                        "exactPath": False,
                        "extraPath": [],
                    },
                },
                {
                    "title": "Plans de prévention",
                    "item": {
                        "href": "/radiation_protection/riskpreventionplan/",
                        "exactPath": False,
                        "extraPath": None,
                    },
                },
                {
                    "title": "Journaux des emails",
                    "item": {
                        "href": "/log_email/emaillog/",
                        "exactPath": False,
                        "extraPath": [],
                    },
                },
            ],
        },
    ]


@pytest.mark.django_db
def test_get_nav_items_for_staff():
    request = RequestFactory().get("/")
    request.user = auth_factories.StaffUserFactory()
    assert get_nav_items(request) == [
        {
            "title": "Projets",
            "item": {
                "href": "/lab/project/",
                "iconName": "fr-icon-survey-line",
                "extraPath": ["/lab/run/"],
                "exactPath": False,
            },
        },
        {
            "title": "Compte",
            "item": {
                "href": f"/euphro_auth/user/{request.user.id}/change/",
                "iconName": "fr-icon-user-line",
                "exactPath": False,
                "extraPath": [],
            },
        },
    ]
