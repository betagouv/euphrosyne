# emails/providers/mailjet.py
from datetime import datetime

import requests
from django.conf import settings

from .base import BaseEmailProvider

MAILJET_BASE = "https://api.mailjet.com/v3/REST"


class MailjetProvider(BaseEmailProvider):
    def list_messages(self, limit=50):
        url = f"{MAILJET_BASE}/message?ShowContactAlt=true&ShowSubject=true"
        resp = requests.get(
            url,
            auth=(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD),
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
