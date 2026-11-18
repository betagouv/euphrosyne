import datetime
import logging
from typing import cast

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _

from lab.permissions import is_lab_admin

from ..models import User
from .tokens import HermaRefreshToken

logger = logging.getLogger(__name__)


def herma_token_view(request: HttpRequest) -> HttpResponse:
    """Issue a refresh token to paste into Herma, the administrators' upload
    application. Wrapped in ``admin_view`` by the AdminSite; AccountGatesMiddleware
    already requires a verified session from administrators while MFA is
    enforced."""
    user = cast(User, request.user)
    if not is_lab_admin(user):
        raise PermissionDenied
    context = {
        **admin.site.each_context(request),
        "title": _("Herma token"),
    }
    if request.method == "POST":
        refresh = HermaRefreshToken.for_user(user)
        logger.info("Herma token issued for user %s (jti %s)", user.pk, refresh["jti"])
        context["refresh_token"] = str(refresh)
        context["expires_at"] = timezone.localtime(
            datetime.datetime.fromtimestamp(refresh["exp"], tz=datetime.UTC)
        )
    return render(request, "euphro_auth/herma_token.html", context)
