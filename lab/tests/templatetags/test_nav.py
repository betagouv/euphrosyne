import json
from unittest import mock

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from lab.templatetags.nav import nav_items_json


# pylint: disable=too-many-arguments
def _check_nav_item(item, title, href, extra_path, exact_path, icon_name=None):
    assert item["title"] == str(title)
    assert "item" in item
    assert item["item"]["href"] == href
    assert item["item"]["extraPath"] == extra_path
    assert item["item"]["exactPath"] == exact_path
    if icon_name:
        assert item["item"]["iconName"] == icon_name


def test_nav_items_json_when_user():
    data = json.loads(
        nav_items_json(
            mock.MagicMock(
                user=User(is_lab_admin=False, is_superuser=False, id=1),
                path="/path",
            )
        )
    )
    assert len(data["items"]) == 2

    _check_nav_item(
        data["items"][0],
        _("Projects"),
        reverse("admin:lab_project_changelist"),
        [reverse("admin:lab_run_changelist")],
        False,
        "fr-icon-survey-line",
    )
    _check_nav_item(
        data["items"][1],
        _("Account"),
        reverse("admin:euphro_auth_user_change", args=[1]),
        [],
        False,
    )

    assert data["currentPath"] == "/path"


def test_nav_items_json_when_admin():
    data = json.loads(
        nav_items_json(
            mock.MagicMock(user=mock.MagicMock(is_lab_admin=True), path="/path")
        )
    )
    assert len(data["items"]) == 4

    dashboard = data["items"][0]
    _check_nav_item(
        dashboard,
        _("Dashboard"),
        reverse("admin:index"),
        [],
        True,
        "fr-icon-calendar-line",
    )

    projects = data["items"][1]
    _check_nav_item(
        projects,
        _("Projects"),
        reverse("admin:lab_project_changelist"),
        [reverse("admin:lab_run_changelist")],
        False,
        "fr-icon-survey-line",
    )

    users = data["items"][2]
    _check_nav_item(
        users,
        _("Users"),
        reverse("admin:euphro_auth_user_changelist"),
        [reverse("admin:euphro_auth_userinvitation_changelist")],
        False,
        "fr-icon-user-line",
    )

    assert data["items"][3]["title"] == str(_("Certifications"))

    certifications = data["items"][3]["items"][0]
    _check_nav_item(
        certifications,
        _("Certifications"),
        reverse("admin:certification_certification_changelist"),
        [],
        False,
    )

    notifications = data["items"][3]["items"][1]
    _check_nav_item(
        notifications,
        _("Notifications"),
        reverse("admin:certification_certificationnotification_changelist"),
        [],
        False,
    )

    results = data["items"][3]["items"][2]
    _check_nav_item(
        results,
        _("Results"),
        reverse("admin:certification_quizresult_changelist"),
        [],
        False,
    )

    assert data["currentPath"] == "/path"
