from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _

from lab.nav import NavElementJson
from lab.permissions import is_lab_admin


def get_nav_items(request: HttpRequest) -> list[NavElementJson]:
    items: list[NavElementJson] = []
    if is_lab_admin(request.user):
        items.append(
            {
                "title": _("Prevention plans"),
                "item": {
                    "href": reverse(
                        "admin:radiation_protection_riskpreventionplan_changelist"
                    ),
                    "exactPath": False,
                    "extraPath": None,
                },
            }
        )
    return items
