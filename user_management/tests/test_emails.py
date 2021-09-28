from django.test import TestCase
from django.core import mail
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ..emails import send_invitation_email


class InvitationEmailTests(TestCase):
    def test_send_email(self):
        user_id = 1
        uid = urlsafe_base64_encode(force_bytes(user_id))
        token = ("atomuf-7385216b60f010e10273a27ba66d6f93",)

        send_invitation_email(
            email="test@test.com",
            user_id=user_id,
            token=token,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "[Euphrosyne] Invitation to register")
        self.assertIn(
            f"{settings.SITE_URL}/registration/{uid}/{token}/", mail.outbox[0].body
        )
