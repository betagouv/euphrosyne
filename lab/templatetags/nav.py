import json

from django import template
from django.conf import settings
from django.http import HttpRequest

from ..nav import NavItemJson

register = template.Library()


@register.simple_tag()
def nav_items_json(request: HttpRequest):
    items: list[NavItemJson] = settings.NAV_GET_NAV_ITEMS(request)

    data = json.dumps({"currentPath": request.path, "items": items})
    return data
