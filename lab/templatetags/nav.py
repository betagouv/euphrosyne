import json

from django import template
from django.conf import settings
from django.http import HttpRequest

from euphrosyne.features import FEATURE_APPS

from ..nav import NavElementJson

register = template.Library()


@register.simple_tag()
def nav_items_json(request: HttpRequest):
    items: list[NavElementJson] = settings.NAV_GET_NAV_ITEMS(request)

    data = json.dumps({"currentPath": request.path, "items": items})
    return data


@register.simple_tag()
def feature_flags_json():
    enabled_features = set(getattr(settings, "EUPHROSYNE_FEATURES", []))
    flags = {feature: feature in enabled_features for feature in FEATURE_APPS}
    return json.dumps(flags)
