import datetime
import logging
from typing import cast

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from lab.permissions import is_lab_admin

from ..mfa import services as mfa_services
from ..models import User
from .tokens import EuphroRefreshToken

logger = logging.getLogger(__name__)


def herma_token_view(request: HttpRequest) -> HttpResponse:
    """Issue a refresh token for the Herma desktop application.

    Herma is used by administrators only, and the session must be verified with
    a second factor while MFA is enforced. Wrapped in ``admin_view`` by the
    AdminSite."""
    user = cast(User, request.user)
    if not is_lab_admin(user):
        raise PermissionDenied
    verified = mfa_services.is_verified(user)
    if not verified and settings.MFA_ADMIN_REQUIRED:
        return redirect(mfa_services.get_mfa_url(user, request.get_full_path()))

    context = {
        **admin.site.each_context(request),
        "title": _("Herma token"),
    }
    if request.method == "POST":
        refresh = EuphroRefreshToken.for_user(user)
        refresh["mfa"] = verified
        logger.info(
            "Herma token issued for user %s (jti %s)",
            user.pk,
            refresh.get("jti"),
        )
        context["refresh_token"] = str(refresh)
        context["expires_at"] = timezone.localtime(
            datetime.datetime.fromtimestamp(refresh["exp"], tz=datetime.timezone.utc)
        )
    return render(request, "euphro_auth/herma_token.html", context)
