from django import template
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

from euphro_auth.models import User
from euphrosyne.features import FEATURE_APPS

from ..nav import NavElementJson

register = template.Library()


@register.simple_tag()
def nav_items_json(request: HttpRequest):
    items: list[NavElementJson] = settings.NAV_GET_NAV_ITEMS(request)

    return {"currentPath": request.path, "items": items}


@register.simple_tag()
def feature_flags_json():
    enabled_features = set(getattr(settings, "EUPHROSYNE_FEATURES", []))
    flags = {feature: feature in enabled_features for feature in FEATURE_APPS}
    return flags


@register.simple_tag
def user_json_data(user: User):
    return {
        "fullName": user.get_full_name(),
        "isLabAdmin": user.is_lab_admin,
        "id": user.id,
        "accountURL": reverse("admin:euphro_auth_user_change", args=[user.id]),
        "email": user.email,
    }
