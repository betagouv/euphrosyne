from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from certification.providers.tally.hooks import tally_webhook as base_tally_webhook
from radiation_protection.app_settings import settings as app_settings


# The exposed view must allow Tally POSTs without a browser CSRF token. The shared
# handler checks the signing secret and HMAC before parsing or modifying data.
@csrf_exempt
@require_POST
def tally_webhook(request: HttpRequest) -> JsonResponse:
    return base_tally_webhook(
        request, getattr(app_settings, "RADIATION_PROTECTION_TALLY_SECRET_KEY", None)
    )
