from allauth.idp.oidc.models import Client
from django.conf import settings
from django.core.management.base import BaseCommand

from ...jwt.authentication import EUPHROSYNE_BACKEND_SCOPE
from ...jwt.signing import TOOLS_SCOPE


def _clients() -> dict[str, dict]:
    return {
        settings.OIDC_HERMA_CLIENT_ID: {
            "name": "Herma",
            "type": Client.Type.PUBLIC,
            "grant_types": [
                Client.GrantType.DEVICE_CODE,
                Client.GrantType.REFRESH_TOKEN,
            ],
            "scopes": ["openid", TOOLS_SCOPE],
            "skip_consent": False,
        },
        settings.OIDC_TOOLS_API_CLIENT_ID: {
            "name": "Euphrosyne Tools API",
            "type": Client.Type.CONFIDENTIAL,
            "grant_types": [Client.GrantType.CLIENT_CREDENTIALS],
            "scopes": [EUPHROSYNE_BACKEND_SCOPE],
            "skip_consent": True,
            "secret": settings.OIDC_TOOLS_API_CLIENT_SECRET,
        },
    }


class Command(BaseCommand):
    help = (
        "Create or update the OpenID Connect clients (Herma, Tools API). "
        "The Tools API's secret comes from OIDC_TOOLS_API_CLIENT_SECRET."
    )

    def handle(self, *args, **options):
        for client_id, config in _clients().items():
            # A new client gets a random secret nobody knows, kept until a
            # secret is configured.
            client, created = Client.objects.get_or_create(id=client_id)
            client.name = config["name"]
            client.type = config["type"]
            client.set_grant_types(config["grant_types"])
            client.set_scopes(config["scopes"])
            client.set_default_scopes(config["scopes"])
            client.set_response_types([])
            client.skip_consent = config["skip_consent"]
            secret = config.get("secret")
            if secret and not client.check_secret(secret):
                client.set_secret(secret)
            client.save()
            self.stdout.write(
                f"{'Created' if created else 'Updated'} OIDC client {client_id}."
            )
