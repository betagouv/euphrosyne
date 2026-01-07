from django.apps import apps
from django.http import HttpRequest
from django.utils.translation import gettext as _

from certification.nav import get_nav_items as certification_get_nav_items
from lab.nav import NavElementJson, NavFolderJson
from lab.nav import get_nav_items as lab_get_nav_items
from lab.permissions import is_lab_admin
from log_email.nav import get_nav_items as log_email_get_nav_items


def get_nav_items(request: HttpRequest) -> list[NavElementJson]:
    nav_items = lab_get_nav_items(request)

    if apps.is_installed("data_request"):
        # pylint: disable=import-outside-toplevel
        from data_request.nav import get_nav_items as data_request_get_nav_items

        nav_items += data_request_get_nav_items(request)

    admin_nav_items: NavFolderJson = {
        "title": _("Admin"),
        "items": certification_get_nav_items(request),
    }

    if apps.is_installed("radiation_protection"):
        # pylint: disable=import-outside-toplevel
        from radiation_protection.nav import (
            get_nav_items as radiation_protection_get_nav_items,
        )

        admin_nav_items["items"] += radiation_protection_get_nav_items(request)

    admin_nav_items["items"] += log_email_get_nav_items(request)

    if is_lab_admin(request.user):
        nav_items.append(admin_nav_items)

    return nav_items
