from django.apps import apps
from django.http import HttpRequest

from certification.nav import get_nav_items as certification_get_nav_items
from data_request.nav import get_nav_items as data_request_get_nav_items
from lab.nav import NavElementJson
from lab.nav import get_nav_items as lab_get_nav_items


def get_nav_items(request: HttpRequest) -> list[NavElementJson]:
    nav_items = (
        lab_get_nav_items(request)
        + data_request_get_nav_items(request)
        + certification_get_nav_items(request)
    )
    if apps.is_installed("radiation_protection"):
        # pylint: disable=import-outside-toplevel
        from radiation_protection.nav import (
            get_nav_items as radiation_protection_get_nav_items,
        )

        nav_items += radiation_protection_get_nav_items(request)
    return nav_items
