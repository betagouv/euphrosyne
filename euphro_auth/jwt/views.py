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
from .tokens import HERMA_TOKEN_LIFETIME, EuphroRefreshToken

logger = logging.getLogger(__name__)


def herma_token_view(request: HttpRequest) -> HttpResponse:
    """Issue a refresh token to paste into Herma, the administrators' upload
    application. Wrapped in ``admin_view`` by the AdminSite."""
    user = cast(User, request.user)
    if not is_lab_admin(user):
        raise PermissionDenied
    verified = mfa_services.is_session_verified(request, user)
    if settings.MFA_ADMIN_REQUIRED and not verified:
        return redirect(mfa_services.get_mfa_url(user, request.get_full_path()))

    context = {
        **admin.site.each_context(request),
        "title": _("Herma token"),
    }
    if request.method == "POST":
        refresh = EuphroRefreshToken.for_user(user, mfa=verified)
        refresh.set_exp(lifetime=HERMA_TOKEN_LIFETIME)
        logger.info("Herma token issued for user %s (jti %s)", user.pk, refresh["jti"])
        context["refresh_token"] = str(refresh)
        context["expires_at"] = timezone.localtime(
            datetime.datetime.fromtimestamp(refresh["exp"], tz=datetime.UTC)
        )
    return render(request, "euphro_auth/herma_token.html", context)
