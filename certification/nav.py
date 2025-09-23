from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _

from lab.nav import NavElementJson
from lab.permissions import is_lab_admin


def get_nav_items(request: HttpRequest) -> list[NavElementJson]:
    items: list[NavElementJson] = []
    if request.user and is_lab_admin(request.user):
        items.append(
            {
                "title": str(_("Certifications")),
                "item": {
                    "href": reverse("admin:certification_certification_changelist"),
                    "exactPath": False,
                    "extraPath": [],
                },
            }
        )
    return items
