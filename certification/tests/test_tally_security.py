import base64
import hmac
import json
from unittest import mock

import pytest
from django.test import Client, RequestFactory
from django.urls import resolve, reverse

from certification.certifications.models import (
    Certification,
    CertificationType,
    QuizCertification,
    QuizResult,
)
from certification.notifications.models import CertificationNotification
from certification.providers.tally.hooks import _validate_signature
from certification.providers.tally.hooks import tally_webhook as provider_webhook
from certification.providers.tally.tests._mock import get_tally_data
from lab.tests.factories import StaffUserFactory
from radiation_protection.app_settings import settings as app_settings
from radiation_protection.tally import tally_webhook as exposed_webhook

SIGNING_SECRET = "tally-security-test-only"


def sign(body: bytes, secret: str = SIGNING_SECRET) -> str:
    return base64.b64encode(hmac.digest(secret.encode(), body, "sha256")).decode()


@pytest.fixture(name="webhook_context")
def _webhook_context(db, monkeypatch):  # pylint: disable=unused-argument
    monkeypatch.setattr(
        app_settings, "RADIATION_PROTECTION_TALLY_SECRET_KEY", SIGNING_SECRET
    )
    certification = Certification.objects.create(
        name="signed-quiz", type_of=CertificationType.QUIZ
    )
    QuizCertification.objects.create(
        certification=certification, passing_score=10, url="https://quiz.test"
    )
    user = StaffUserFactory(first_name="Original", last_name="Name")
    payload = get_tally_data(user.email, 11)
    payload["data"]["fields"].extend(
        [
            {
                "key": "first",
                "label": "First name",
                "type": "INPUT_TEXT",
                "value": "Éva",
            },
            {
                "key": "last",
                "label": "Last name",
                "type": "INPUT_TEXT",
                "value": "Updated",
            },
        ]
    )
    body = json.dumps(payload, ensure_ascii=False).encode()
    headers = {
        "Tally-Signature": sign(body),
        "Euphrosyne-Certification": certification.name,
        "Euphrosyne-QuizUrl": "https://quiz.test",
    }
    return user, body, headers


@pytest.fixture(
    name="webhook_client", params=[False, True], ids=["anonymous", "session"]
)
def _webhook_client(request, webhook_context):
    client = Client(enforce_csrf_checks=True)
    if request.param:
        client.force_login(webhook_context[0])
    return client


def assert_no_side_effects(user):
    user.refresh_from_db()
    assert (user.first_name, user.last_name) == ("Original", "Name")
    assert not QuizResult.objects.exists()
    assert not CertificationNotification.objects.exists()


def test_exposed_webhook_accepts_signed_body(webhook_context, webhook_client):
    user, body, headers = webhook_context
    url = reverse("tally_webhook")
    assert resolve(url).func is exposed_webhook
    response = webhook_client.post(
        url, data=body, content_type="application/json", headers=headers
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    user.refresh_from_db()
    assert (user.first_name, user.last_name) == ("Éva", "Updated")
    result = QuizResult.objects.get(user=user)
    assert result.score == 11
    assert result.is_passed
    assert CertificationNotification.objects.filter(
        user=user, quiz_result=result
    ).exists()


@pytest.mark.parametrize(
    "signature_case",
    [
        "missing",
        "empty",
        "wrong-secret",
        "invalid-base64",
        "unicode",
        "short",
        "unpadded",
        "extra-padding",
        "whitespace",
        "altered-score",
        "altered-whitespace",
        "invalid-json",
    ],
)
def test_exposed_webhook_rejects_untrusted_body(
    webhook_context, webhook_client, signature_case
):
    user, body, headers = webhook_context
    signature = headers["Tally-Signature"]
    if signature_case == "missing":
        headers.pop("Tally-Signature")
    elif signature_case == "altered-score":
        body = body.replace(b'"value": 11', b'"value": 99')
    elif signature_case == "altered-whitespace":
        body += b" "
    elif signature_case == "invalid-json":
        body = b"not json"
    else:
        headers["Tally-Signature"] = {
            "empty": "",
            "wrong-secret": sign(body, "another-test-secret"),
            "invalid-base64": "!" * 44,
            "unicode": "é" * 44,
            "short": base64.b64encode(b"short").decode(),
            "unpadded": signature.rstrip("="),
            "extra-padding": signature + "=",
            "whitespace": signature + " ",
        }[signature_case]

    with (
        mock.patch(
            "certification.providers.tally.hooks.TallyWebhookData.from_tally_data"
        ) as parse,
        mock.patch(
            "certification.providers.tally.hooks._update_user_name_with_form"
        ) as update,
        mock.patch("certification.providers.tally.hooks.create_quiz_result") as create,
    ):
        response = webhook_client.post(
            reverse("tally_webhook"),
            data=body,
            content_type="application/json",
            headers=headers,
        )
    assert response.status_code == 403
    assert response.json() == {"error": "Invalid signature"}
    parse.assert_not_called()
    update.assert_not_called()
    create.assert_not_called()
    assert_no_side_effects(user)


@pytest.mark.parametrize("secret", [None, ""])
def test_exposed_webhook_without_secret_is_unavailable(
    webhook_context, webhook_client, monkeypatch, secret, caplog
):
    user, body, headers = webhook_context
    monkeypatch.setattr(app_settings, "RADIATION_PROTECTION_TALLY_SECRET_KEY", secret)
    # Even an HMAC calculated with the publicly known empty key must be refused.
    headers["Tally-Signature"] = sign(body, "")
    with (
        mock.patch(
            "certification.providers.tally.hooks.TallyWebhookData.from_tally_data"
        ) as parse,
        mock.patch(
            "certification.providers.tally.hooks._update_user_name_with_form"
        ) as update,
        mock.patch("certification.providers.tally.hooks.create_quiz_result") as create,
    ):
        response = webhook_client.post(
            reverse("tally_webhook"),
            data=body,
            content_type="application/json",
            headers=headers,
        )
    assert response.status_code == 503
    assert response.json() == {"error": "Webhook unavailable"}
    assert "signing secret is not configured; processing disabled" in caplog.text
    assert SIGNING_SECRET not in caplog.text
    assert headers["Tally-Signature"] not in caplog.text
    assert user.email not in caplog.text
    parse.assert_not_called()
    update.assert_not_called()
    create.assert_not_called()
    assert_no_side_effects(user)


@pytest.mark.parametrize("secret", [None, ""])
def test_provider_cannot_validate_or_process_without_secret(secret):
    body = b"not json"
    request = RequestFactory().post(
        "/webhook",
        data=body,
        content_type="application/json",
        headers={"Tally-Signature": sign(body, "")},
    )
    assert not _validate_signature(request, secret)
    assert provider_webhook(request, secret).status_code == 503


def test_provider_accepts_real_signature(webhook_context):
    user, body, headers = webhook_context
    request = RequestFactory().post(
        "/webhook", data=body, content_type="application/json", headers=headers
    )
    assert _validate_signature(request, SIGNING_SECRET)
    assert provider_webhook(request, SIGNING_SECRET).status_code == 200
    assert QuizResult.objects.filter(user=user).exists()


@pytest.mark.parametrize("handler", [provider_webhook, exposed_webhook])
def test_webhooks_require_post(handler):
    request = RequestFactory().get("/webhook")
    response = (
        handler(request, SIGNING_SECRET)
        if handler is provider_webhook
        else handler(request)
    )
    assert response.status_code == 405
