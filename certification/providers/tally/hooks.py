# pylint: disable=invalid-name

import base64
import hashlib
import hmac
import json
import logging

from django.contrib.auth import get_user_model
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from certification.certifications.models import QuizCertification
from certification.providers.tally.dataclasses import TallyWebhookData

from ...certifications.results import create_quiz_result
from ...models import Certification

logger = logging.getLogger(__name__)


def _validate_signature(request: HttpRequest, secret_key: str | None) -> bool:
    if not secret_key:
        return False

    # Get the Tally-Signature header value
    signature_header = request.headers.get("Tally-Signature")

    if not signature_header:
        return False

    try:
        signature = signature_header.encode("ascii")
    except UnicodeEncodeError:
        return False

    digest = hmac.new(
        secret_key.encode("utf-8"), request.body, digestmod=hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest)
    # Comparing the canonical base64 also rejects malformed signature encodings.
    return hmac.compare_digest(computed_hmac, signature)


# Server-to-server webhook: HMAC authenticates the raw body before any side effect.
@csrf_exempt
@require_POST
def tally_webhook(
    request: HttpRequest, secret_key: str | None
):  # pylint: disable=too-many-return-statements
    if not secret_key:
        logger.error(
            "Tally webhook : signing secret is not configured; processing disabled"
        )
        return JsonResponse({"error": "Webhook unavailable"}, status=503)

    is_signature_valid = _validate_signature(request, secret_key)
    if not is_signature_valid:
        logger.error("Tally webhook : invalid signature")
        return JsonResponse({"error": "Invalid signature"}, status=403)

    # Get certificate name from GET data
    certificate_name = request.headers.get("Euphrosyne-Certification")
    if not certificate_name:
        logger.error("Tally webhook : certificate name is required")
        return JsonResponse({"error": "Certificate name is required"}, status=400)

    quiz_url = request.headers.get("Euphrosyne-QuizUrl")
    if not quiz_url:
        logger.error("Tally webhook : quiz url is required")
        return JsonResponse({"error": "quiz url is required"}, status=400)

    data = TallyWebhookData.from_tally_data(json.loads(request.body))

    email = data.user_email
    if not email:
        logger.error("Tally webhook : email is required for %s", certificate_name)
        return JsonResponse({"error": "Email is required"}, status=400)
    score = data.score
    if score is None:
        logger.error("Tally webhook : score is required for %s", certificate_name)
        return JsonResponse({"error": "Score is required"}, status=400)

    _update_user_name_with_form(data)

    try:
        create_quiz_result(
            certification_name=certificate_name,
            quiz_url=quiz_url,
            email=email,
            score=score,
        )
    except Certification.DoesNotExist:
        logger.error(
            "Tally webhook : certification %s not found in DB", certificate_name
        )
        return JsonResponse({"error": "Certification not found"}, status=400)
    except QuizCertification.DoesNotExist:
        logger.error(
            "Tally webhook : quiz certification with %s not found in DB", quiz_url
        )
        return JsonResponse({"error": "Quiz with url not found"}, status=400)

    return JsonResponse({"status": "success"})


def _update_user_name_with_form(data: TallyWebhookData):
    """Update user name based on Tally form data."""
    fields = data.data.fields
    first_name = next(
        (field.value for field in fields if field.label == "First name"), None
    )
    last_name = next(
        (field.value for field in fields if field.label == "Last name"), None
    )

    if first_name and last_name:
        user = get_user_model().objects.filter(email=data.user_email).first()
        if user:
            user.first_name = first_name  # type: ignore
            user.last_name = last_name  # type: ignore
            user.save()
        else:
            logger.warning(
                "Tally webhook : user with email %s not found, cannot update name",
                data.user_email,
            )
