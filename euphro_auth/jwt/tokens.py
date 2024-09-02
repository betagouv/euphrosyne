from rest_framework_simplejwt.settings import api_settings as rf_simplejwt_api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from lab.permissions import is_lab_admin

from ..models import User


class EuphroRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user: User):  # type: ignore[override]
        token = super().for_user(user)
        token["projects"] = list(
            user.project_set.values("id", "name", "slug")  # type: ignore[misc]
        )
        token["is_admin"] = is_lab_admin(user)
        return token


class EuphroToolsAPIToken(RefreshToken):
    """Token used for direct communication between Euphrosyne & Euphrosyne Tools."""

    @classmethod
    def for_euphrosyne(cls):
        token = cls()
        token[rf_simplejwt_api_settings.USER_ID_CLAIM] = "euphrosyne"
        return token
