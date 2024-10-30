import json
from typing import TypedDict

from django import template
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from lab.permissions import is_lab_admin

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
            items.append(
                {
                    "title": str(_("Certifications")),
                    "items": [
                        {
                            "title": str(_("Certifications")),
                            "item": {
                                "href": reverse(
                                    "admin:certification_certification_changelist"
                                ),
                                "exactPath": False,
                                "extraPath": [],
                            },
                        },
                        {
                            "title": str(_("Notifications")),
                            "item": {
                                "href": reverse(
                                    # pylint: disable=line-too-long
                                    "admin:certification_certificationnotification_changelist"
                                ),
                                "exactPath": False,
                                "extraPath": [],
                            },
                        },
                        {
                            "title": str(_("Results")),
                            "item": {
                                "href": reverse(
                                    "admin:certification_quizresult_changelist"
                                ),
                                "exactPath": False,
                                "extraPath": [],
                            },
                        },
                    ],
                }
            )
        else:  # non-admin user
            items.append(
                {
                    "title": str(_("Account")),
                    "item": {
                        "href": reverse(
                            "admin:euphro_auth_user_change", args=[request.user.id]
                        ),
                        "iconName": "fr-icon-user-line",
                        "exactPath": False,
                        "extraPath": [],
                    },
                }
            )

    data = json.dumps({"currentPath": request.path, "items": items})
    return data
