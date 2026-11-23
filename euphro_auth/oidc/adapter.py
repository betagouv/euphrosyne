from typing import Any

from allauth.idp.oidc.adapter import DefaultOIDCAdapter
from django.conf import settings

from ..jwt.claims import user_claims


class EuphroOIDCAdapter(DefaultOIDCAdapter):
    def get_issuer(self) -> str:
        # The site URL rather than the request's host: tokens are also signed
        # outside a request (management commands), and the Tools API compares
        # the issuer with the URL it calls Euphrosyne at.
        return settings.SITE_URL.rstrip("/")

    def populate_access_token(
        self, access_token: dict[str, Any], *, client, scopes, user, **kwargs: Any
    ) -> None:
        # Also called on refresh: a demoted administrator loses ``is_admin``
        # within an access token lifetime.
        if user is not None:
            access_token.update(user_claims(user))
