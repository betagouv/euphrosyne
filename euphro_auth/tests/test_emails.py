from django.core import mail
from django.test.testcases import SimpleTestCase
from django.utils.translation import gettext

from euphro_auth.models import User

from ..emails import send_invitation_email


class InvitationEmailTests(SimpleTestCase):
    def test_send_email(self):

        send_invitation_email(user=User(id=1, email="test@test.com"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, gettext("[Euphrosyne] Invitation to register")
        )
        self.assertRegex(mail.outbox[0].body, r"\/registration\/MQ\/.{39,45}\/")
