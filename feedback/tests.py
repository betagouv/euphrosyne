from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status


@pytest.mark.django_db
def test_feedback_view_send_mail(client, settings):
    settings.DEFAULT_FROM_EMAIL = "no-reply@example.com"
    settings.FEEDBACK_EMAILS = ["feedback@example.com"]

    data = {
        "email": "user@example.com",
        "message": "This is a feedback message.",
        "name": "User",
    }
    files = {
        "file": SimpleUploadedFile(
            "file.txt", b"file_content", content_type="text/plain"
        )
    }

    with mock.patch("django.core.mail.EmailMessage.send") as send_mail_mock:
        response = client.post("/api/feedback/", data, format="multipart", files=files)
        assert response.status_code == status.HTTP_200_OK
        send_mail_mock.assert_called_once()


@pytest.mark.django_db
def test_feedback_view_invalid_data_blank_message(client):
    data = {
        "email": "user@example.com",
        "message": "",
        "name": "User",
    }

    response = client.post("/api/feedback/", data, format="multipart")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
