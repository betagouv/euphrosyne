from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from certification.providers.tally.hooks import tally_webhook as base_tally_webhook
from radiation_protection.app_settings import settings as app_settings


@csrf_exempt
@require_POST
def tally_webhook(request: HttpRequest) -> JsonResponse:
    return base_tally_webhook(
        request, app_settings.RADIATION_PROTECTION_TALLY_SECRET_KEY
    )
