from datetime import timedelta

from django.conf import settings
from rest_framework_simplejwt.settings import api_settings as rf_simplejwt_api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from lab.permissions import is_lab_admin

from ..models import User


class EuphroRefreshToken(RefreshToken):
    @classmethod
    def for_user(  # type: ignore[override] # pylint: disable=arguments-differ
        cls, user: User, *, mfa: bool
    ):
        """``mfa``: whether the session issuing the token went through a second
        factor. Administrator rights (``is_admin``, used by the Tools API) are
        granted only then, or when MFA is not enforced."""
        token = super().for_user(user)
        token["projects"] = list(
            user.project_set.values("id", "name", "slug")  # type: ignore[misc]
        )
        token["mfa"] = mfa
        token["is_admin"] = is_lab_admin(user) and (
            mfa or not settings.MFA_ADMIN_REQUIRED
        )
        # because https://github.com/jazzband/djangorestframework-simplejwt/pull/887
        token["user_id"] = int(token["user_id"])
        return token


class HermaRefreshToken(EuphroRefreshToken):
    """Refresh token pasted into Herma, the administrators' upload application.
    Its one-day validity is chosen for Herma, independently of the default
    refresh token lifetime."""

    lifetime = timedelta(days=1)


class EuphroToolsAPIToken(RefreshToken):
    """Token used for direct communication between Euphrosyne & Euphrosyne Tools."""

    @classmethod
    def for_euphrosyne(cls):
        token = cls()
        token[rf_simplejwt_api_settings.USER_ID_CLAIM] = "euphrosyne"
        token["projects"] = []
        token["is_admin"] = True
        return token
