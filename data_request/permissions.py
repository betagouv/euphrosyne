import logging
from urllib.parse import urlsplit

from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission

logger = logging.getLogger(__name__)


def normalize_origin(origin: str) -> str:
    parsed_origin = urlsplit(origin.strip())
    if not parsed_origin.scheme or not parsed_origin.netloc:
        return ""
    return f"{parsed_origin.scheme}://{parsed_origin.netloc}"


class DataRequestOriginPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        allowed_origins = {
            normalized_origin
            for origin in settings.DATA_REQUEST_ALLOWED_ORIGINS
            if (normalized_origin := normalize_origin(origin))
        }
        if not allowed_origins:
            return True

        request_origin = request.headers.get("Origin")
        if request_origin and normalize_origin(request_origin) in allowed_origins:
            return True

        logger.warning(
            "Rejected data request submission because Origin is not allowed "
            "endpoint=%s origin=%s",
            request.path,
            request_origin,
        )
        return False
