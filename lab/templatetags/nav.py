import json
from typing import TypedDict

from django import template
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

register = template.Library()


class NavItemJson(TypedDict):
    title: str
    href: str
    iconName: str
    extraPath: list[str] | None
    exactPath: bool
    badge: int | None


@register.simple_tag()
def nav_items_json(request: HttpRequest):
    items: list[NavItemJson] = [
        {
            "title": str(_("Projects")),
            "href": reverse("admin:lab_project_changelist"),
            "iconName": "fr-icon-survey-line",
            "extraPath": [reverse("admin:lab_run_changelist")],
            "exactPath": False,
        }
    ]

    if request.user and request.user.is_lab_admin:
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
                "extraPath": [],
            }
        )
        items.append(
            {
                "title": str(_("Invitations")),
                "href": reverse("admin:euphro_auth_userinvitation_changelist"),
                "iconName": "fr-icon-mail-line",
                "exactPath": False,
                "extraPath": [],
            }
        )

    data = json.dumps({"currentPath": request.path, "items": items})
    return data
