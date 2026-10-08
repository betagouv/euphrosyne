# emails/providers/mailjet.py
from collections.abc import Mapping
from datetime import datetime
from typing import Any, cast

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import BaseEmailProvider

MAILJET_BASE = "https://api.mailjet.com/v3/REST"


def _get_mailjet_auth() -> tuple[str, str]:
    mailjet_configs = []
    mailers = cast(Mapping[str, Mapping[str, Any]], settings.MAILERS)
    for alias, config in mailers.items():
        options = cast(Mapping[str, Any], config.get("OPTIONS", {}))
        host = options.get("host", "")
        if isinstance(host, str) and "mailjet" in host.casefold():
            mailjet_configs.append((alias, options))

    if not mailjet_configs:
        raise ImproperlyConfigured("No Mailjet configuration found in MAILERS.")
    if len(mailjet_configs) > 1:
        aliases = ", ".join(alias for alias, _options in mailjet_configs)
        raise ImproperlyConfigured(
            f"Multiple Mailjet configurations found in MAILERS: {aliases}."
        )

    alias, options = mailjet_configs[0]
    try:
        return options["username"], options["password"]
    except KeyError as error:
        raise ImproperlyConfigured(
            f"Mailer {alias!r} must define {error.args[0]!r} in OPTIONS."
        ) from error


class MailjetProvider(BaseEmailProvider):
    def list_messages(self, limit=50):
        url = f"{MAILJET_BASE}/message?ShowContactAlt=true&ShowSubject=true"
        resp = requests.get(
            url,
            auth=_get_mailjet_auth(),
            params={"Limit": limit, "Sort": "ArrivedAt DESC"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json().get("Data", [])
        return [
            {
                "id": str(m["ID"]),
                "to": m.get("ContactAlt", ""),
                "subject": m.get("Subject", ""),
                "status": m.get("Status", ""),
                "date": datetime.fromisoformat(m["ArrivedAt"].replace("Z", "+00:00")),
            }
            for m in data
        ]
