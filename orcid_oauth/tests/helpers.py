"""Drive the real ORCID sign-in flow, mocking only ORCID's HTTP responses."""

from unittest.mock import patch

from allauth.socialaccount.internal.statekit import STATES_SESSION_KEY
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.orcid.views import OrcidOAuth2Adapter
from django.test import Client
from django.urls import reverse

DEFAULT_UID = "0000-0002-1234-5678"


def start_orcid_login(client: Client, data: dict | None = None, query: str = ""):
    return client.post(
        f"{reverse('orcid_login')}{query}", {"process": "login", **(data or {})}
    )


def latest_oauth_state(client: Client) -> str:
    return next(reversed(client.session[STATES_SESSION_KEY]))


def orcid_record(uid: str, **names: str) -> dict:
    return {
        "orcid-identifier": {"path": uid, "uri": f"https://orcid.org/{uid}"},
        "person": {
            "name": {
                "given-names": {"value": names.get("first_name", "ORCID")},
                "family-name": {"value": names.get("last_name", "User")},
            },
            "emails": {"email": []},
        },
    }


def orcid_callback(
    client: Client,
    uid: str = DEFAULT_UID,
    *,
    state: str | None = None,
    data: dict | None = None,
):
    def complete_login(adapter, request, app, token, **kwargs):
        # pylint: disable=unused-argument
        return adapter.get_provider().sociallogin_from_response(
            request, orcid_record(uid)
        )

    with (
        patch.object(
            OAuth2Client,
            "get_access_token",
            return_value={
                "orcid": uid,
                "access_token": "test-access-token",
                "token_type": "bearer",
            },
        ),
        patch.object(OrcidOAuth2Adapter, "complete_login", complete_login),
    ):
        return client.get(
            reverse("orcid_callback"),
            {
                "state": state or latest_oauth_state(client),
                "code": "valid-test-code",
                **(data or {}),
            },
        )
