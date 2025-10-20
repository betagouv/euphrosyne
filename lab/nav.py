import typing

from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _

from lab.permissions import is_lab_admin


class NavItemInfoJson(typing.TypedDict):
    href: str
    iconName: typing.NotRequired[str]
    extraPath: list[str] | None
    exactPath: bool
    badge: typing.NotRequired[int | None]


class NavItemJson(typing.TypedDict):
    title: str
    item: NavItemInfoJson


class NavFolderJson(typing.TypedDict):
    title: str
    items: list[typing.Union[NavItemJson, "NavFolderJson"]]


NavElementJson = typing.Union[NavItemJson, NavFolderJson]


def get_nav_items(request: HttpRequest) -> list[NavElementJson]:
    items: list[NavElementJson] = [
        {
            "title": str(_("Projects")),
            "item": {
                "href": reverse("admin:lab_project_changelist"),
                "iconName": "fr-icon-survey-line",
                "extraPath": [reverse("admin:lab_run_changelist")],
                "exactPath": False,
            },
        }
    ]

    if request.user:
        if is_lab_admin(request.user):
            items.insert(
                0,
                {
                    "title": str(_("Dashboard")),
                    "item": {
                        "href": reverse("admin:index"),
                        "iconName": "fr-icon-calendar-line",
                        "exactPath": True,
                        "extraPath": [],
                    },
                },
            )
            items.append(
                {
                    "title": str(_("Users")),
                    "item": {
                        "href": reverse("admin:euphro_auth_user_changelist"),
                        "iconName": "fr-icon-user-line",
                        "exactPath": False,
                        "extraPath": [
                            reverse("admin:euphro_auth_userinvitation_changelist")
                        ],
                    },
                }
            )
    return items
