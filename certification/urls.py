from django.apps import apps
from django.urls import path

urlpatterns = []

if apps.is_installed("radiation_protection"):
    # pylint: disable=import-outside-toplevel
    from radiation_protection.tally import tally_webhook

    urlpatterns.append(path("hooks/tally", tally_webhook, name="tally_webhook"))
