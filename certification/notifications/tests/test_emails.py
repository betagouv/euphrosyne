from unittest import mock

from django.core import mail
from django.test import SimpleTestCase
from django.utils.translation import gettext

from ..emails import send_notification


class NotificationsEmailTests(SimpleTestCase):

    def test_send_notification(self):
        with mock.patch(
            "certification.notifications.emails.render_to_string"
        ) as mock_fn:
            mock_fn.return_value = "html_message"
            send_notification(
                email="email@test.fr",
                template_path="path/to/template",
                certification_name="certification",
                context={},
            )

            assert len(mail.outbox) == 1
            assert mail.outbox[0].subject == gettext(
                "[Euphrosyne] Invitation to complete certification certification."
            )
            assert mail.outbox[0].body == "html_message"
