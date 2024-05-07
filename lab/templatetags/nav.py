import json

from django import template
from django.conf import settings
from django.http import HttpRequest

from ..nav import NavElementJson

register = template.Library()


@register.simple_tag()
def nav_items_json(request: HttpRequest):
    items: list[NavElementJson] = settings.NAV_GET_NAV_ITEMS(request)

    data = json.dumps({"currentPath": request.path, "items": items})
    return data
