import typing

from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _

from lab.permissions import is_lab_admin


class NavItemJson(typing.TypedDict):
    title: str
    href: str
    iconName: str
    extraPath: list[str] | None
    exactPath: bool
    badge: typing.NotRequired[int | None]


def get_nav_items(request: HttpRequest) -> list[NavItemJson]:
    items: list[NavItemJson] = [
        {
            "title": str(_("Projects")),
            "href": reverse("admin:lab_project_changelist"),
            "iconName": "fr-icon-survey-line",
            "extraPath": [reverse("admin:lab_run_changelist")],
            "exactPath": False,
        }
    ]

    if request.user:
        if is_lab_admin(request.user):
            items.insert(
                0,
                {
                    "title": str(_("Dashboard")),
                    "href": reverse("admin:index"),
                    "iconName": "fr-icon-calendar-line",
                    "exactPath": True,
                    "extraPath": [],
                },
            )
            items.append(
                {
                    "title": str(_("Users")),
                    "href": reverse("admin:euphro_auth_user_changelist"),
                    "iconName": "fr-icon-user-line",
                    "exactPath": False,
                    "extraPath": [
                        reverse("admin:euphro_auth_userinvitation_changelist")
                    ],
                }
            )
        else:  # non-admin user
            items.append(
                {
                    "title": str(_("Account")),
                    "href": reverse(
                        "admin:euphro_auth_user_change", args=[request.user.id]
                    ),
                    "iconName": "fr-icon-user-line",
                    "exactPath": False,
                    "extraPath": [],
                }
            )
    return items
