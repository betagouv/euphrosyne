from django.http import HttpRequest

from data_request.nav import get_nav_items as data_request_get_nav_items
from lab.nav import NavItemJson
from lab.nav import get_nav_items as lab_get_nav_items


def get_nav_items(request: HttpRequest) -> list[NavItemJson]:
    return lab_get_nav_items(request) + data_request_get_nav_items(request)
