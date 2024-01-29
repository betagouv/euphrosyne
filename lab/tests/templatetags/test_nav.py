import json
from unittest import mock

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from lab.templatetags.nav import nav_items_json


def test_nav_items_json_when_user():
    data = json.loads(
        nav_items_json(
            mock.MagicMock(user=mock.MagicMock(is_lab_admin=False), path="/path")
        )
    )
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == str(_("Projects"))
    assert data["items"][0]["href"] == reverse("admin:lab_project_changelist")
    assert data["items"][0]["iconName"] == "fr-icon-survey-line"
    assert data["items"][0]["extraPath"] == [reverse("admin:lab_run_changelist")]
    assert data["items"][0]["exactPath"] is False

    assert data["currentPath"] == "/path"


def test_nav_items_json_when_admin():
    data = json.loads(
        nav_items_json(
            mock.MagicMock(user=mock.MagicMock(is_lab_admin=True), path="/path")
        )
    )
    assert len(data["items"]) == 4
    assert data["items"][0]["title"] == str(_("Dashboard"))
    assert data["items"][0]["href"] == reverse("admin:index")
    assert data["items"][0]["iconName"] == "fr-icon-calendar-line"
    assert data["items"][0]["extraPath"] == []
    assert data["items"][0]["exactPath"] is True
    assert data["items"][1]["title"] == str(_("Projects"))
    assert data["items"][1]["href"] == reverse("admin:lab_project_changelist")
    assert data["items"][1]["iconName"] == "fr-icon-survey-line"
    assert data["items"][1]["extraPath"] == [reverse("admin:lab_run_changelist")]
    assert data["items"][1]["exactPath"] is False
    assert data["items"][2]["title"] == str(_("Users"))
    assert data["items"][2]["href"] == reverse("admin:euphro_auth_user_changelist")
    assert data["items"][2]["iconName"] == "fr-icon-user-line"
    assert data["items"][2]["extraPath"] == []
    assert data["items"][2]["exactPath"] is False
    assert data["items"][3]["title"] == str(_("Invitations"))
    assert data["items"][3]["href"] == reverse(
        "admin:euphro_auth_userinvitation_changelist"
    )
    assert data["items"][3]["iconName"] == "fr-icon-mail-line"
    assert data["items"][3]["extraPath"] == []
    assert data["items"][3]["exactPath"] is False

    assert data["currentPath"] == "/path"
