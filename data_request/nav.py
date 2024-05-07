from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _

from lab.nav import NavElementJson
from lab.permissions import is_lab_admin

from .models import DataRequest


def get_nav_items(request: HttpRequest) -> list[NavElementJson]:
    items: list[NavElementJson] = []
    if is_lab_admin(request.user):
        items.append(
            {
                "title": _("Data requests"),
                "item": {
                    "href": reverse("admin:data_request_datarequest_changelist"),
                    "iconName": "fr-icon-download-line",
                    "exactPath": False,
                    "extraPath": None,
                    "badge": DataRequest.objects.filter(request_viewed=False).count(),
                },
            }
        )
    return items
