from django.urls import path

from .providers.tally.hooks import tally_webhook

urlpatterns = [path("hooks/tally", tally_webhook, name="tally_webhook")]
