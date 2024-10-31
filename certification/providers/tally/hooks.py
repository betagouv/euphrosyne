# pylint: disable=invalid-name

import base64
import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from certification.providers.tally.dataclasses import TallyWebhookData

from ...certifications.results import create_result
from ...models import Certification

logger = logging.getLogger(__name__)


def _validate_signature(request):
    # Get the Tally-Signature header value
    signature_header = request.headers.get("Tally-Signature")

    secret_key = settings.RADIATION_PROTECTION_TALLY_SECRET_KEY

    digest = hmac.new(
        secret_key.encode("utf-8"), request.body, digestmod=hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, signature_header.encode("utf-8"))


@csrf_exempt
@require_POST
def tally_webhook(request: HttpRequest):
    is_signature_valid = _validate_signature(request)
    if not is_signature_valid:
        logger.error("Tally webhook : invalid signature")
        return JsonResponse({"error": "Invalid signature"}, status=403)

    # Get certificate name from GET data
    certificate_name = request.headers.get("Euphrosyne-Certification")
    if not certificate_name:
        logger.error("Tally webhook : certificate name is required")
        return JsonResponse({"error": "Certificate name is required"}, status=400)

    data = TallyWebhookData.from_tally_data(json.loads(request.body))

    email = data.user_email
    if not email:
        logger.error("Tally webhook : email is required for %s", certificate_name)
        return JsonResponse({"error": "Email is required"}, status=400)
    score = data.score
    if score is None:
        logger.error("Tally webhook : score is required for %s", certificate_name)
        return JsonResponse({"error": "Score is required"}, status=400)

    try:
        create_result(certification_name=certificate_name, email=email, score=score)
    except Certification.DoesNotExist:
        logger.error(
            "Tally webhook : certification %s not found in DB", certificate_name
        )
        return JsonResponse({"error": "Certification not found"}, status=400)

    return JsonResponse({"status": "success"})
