from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from rest_framework_simplejwt.settings import api_settings as rf_simplejwt_api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from lab.permissions import is_lab_admin

from ..models import User


class EuphroRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user: User):  # type: ignore[override]
        """Tokens are issued to a session that went through AccountGatesMiddleware
        (second factor of administrators included): consumers such as the Tools
        API only read ``is_admin``."""
        token = super().for_user(user)
        token["projects"] = list(
            user.project_set.values("id", "name", "slug")  # type: ignore[misc]
        )
        token["is_admin"] = is_lab_admin(user)
        # because https://github.com/jazzband/djangorestframework-simplejwt/pull/887
        token["user_id"] = int(token["user_id"])
        return token


@dataclass(frozen=True)
class TokenService:
    """An application that asks the user to paste a refresh token
    (see euphro_auth.jwt.views.service_token_view)."""

    name: str
    lifetime: timedelta
    allowed: Callable[[User], bool]

    def issue(self, user: User) -> EuphroRefreshToken:
        token = EuphroRefreshToken.for_user(user)
        token.set_exp(lifetime=self.lifetime)
        return token


# Known services, by URL slug: a link cannot make the page show another name.
TOKEN_SERVICES = {
    # Herma, the administrators' upload application.
    "herma": TokenService(
        name="Herma", lifetime=timedelta(days=1), allowed=is_lab_admin
    ),
}


class EuphroToolsAPIToken(RefreshToken):
    """Token used for direct communication between Euphrosyne & Euphrosyne Tools."""

    @classmethod
    def for_euphrosyne(cls):
        token = cls()
        token[rf_simplejwt_api_settings.USER_ID_CLAIM] = "euphrosyne"
        token["projects"] = []
        token["is_admin"] = True
        return token
