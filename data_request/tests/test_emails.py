from django.core import mail
from django.test import SimpleTestCase
from django.utils.translation import gettext

from ..emails import send_data_email, send_data_request_created_email


class DataRequestEmailsTestCase(SimpleTestCase):
    def test_send_data_request_created_email(self):
        send_data_request_created_email("test@test.fr")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == gettext("[New AGLAE] Data request received")
        assert mail.outbox[0].to == ["test@test.fr"]

    def test_send_data_email(self):
        send_data_email(
            "test@test.fr",
            {
                "links": [
                    {
                        "name": "Run 1 (Project 1)",
                        "url": "http://url",
                        "data_type": "raw_data",
                    },
                    {
                        "name": "Run 1 (Project 1)",
                        "url": "http://url",
                        "data_type": "processed_data",
                    },
                ],
                "expiration_date": "2021-07-01 00:00:00",
            },
        )

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == gettext("Your New AGLAE data links")
        assert mail.outbox[0].to == ["test@test.fr"]
