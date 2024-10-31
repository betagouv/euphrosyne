import base64
import hashlib
import hmac
import json
from unittest import mock

from django.test import TestCase, override_settings

from certification.certifications.models import (
    Certification,
    CertificationType,
    QuizCertification,
    QuizResult,
)
from certification.notifications.models import (
    CertificationNotification,
    NotificationType,
)
from lab.tests.factories import StaffUserFactory

from ..providers.tally.hooks import _validate_signature
from ..providers.tally.tests._mock import get_tally_data

PASSING_SCORE = 10


class TestTallyHook(TestCase):
    def setUp(self):
        self.certification = Certification.objects.create(
            name="test", type_of=CertificationType.QUIZ
        )
        QuizCertification.objects.create(
            certification=self.certification, passing_score=PASSING_SCORE
        )

    def test_validate_signature(self):
        request = mock.MagicMock()
        request.body = b"test"

        digest = hmac.new(
            "test".encode("utf-8"), request.body, digestmod=hashlib.sha256
        ).digest()
        computed_hmac = base64.b64encode(digest)

        request.headers = {"Tally-Signature": computed_hmac.decode("utf-8")}
        with override_settings(RADIATION_PROTECTION_TALLY_SECRET_KEY="test"):
            self.assertTrue(_validate_signature(request))

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: False
    )
    def test_validate_signature_invalid(self):
        response = self.client.post(
            "/certification/hooks/tally", data=b"test", content_type="application/json"
        )

        assert response.status_code == 403

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: True
    )
    def test_hook_when_no_certification(self):
        response = self.client.post(
            "/certification/hooks/tally", data=b"test", content_type="application/json"
        )
        assert response.status_code == 400
        assert response.json() == {"error": "Certificate name is required"}

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: True
    )
    @mock.patch("certification.providers.tally.hooks.TallyWebhookData.from_tally_data")
    def test_hook_when_no_email(self, mock_from_tally_data: mock.MagicMock):
        mock_from_tally_data.return_value.user_email = None
        response = self.client.post(
            "/certification/hooks/tally",
            data=b'{"data": {"user_email": null, "score": "test"}}',
            content_type="application/json",
            HTTP_EUPHROSYNE_CERTIFICATION=self.certification.name,
        )
        assert response.status_code == 400
        assert response.json() == {"error": "Email is required"}

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: True
    )
    @mock.patch("certification.providers.tally.hooks.TallyWebhookData.from_tally_data")
    def test_hook_when_no_score(self, mock_from_tally_data: mock.MagicMock):
        mock_from_tally_data.return_value.user_email = "test@test.fr"
        mock_from_tally_data.return_value.score = None
        response = self.client.post(
            "/certification/hooks/tally",
            data=b'{"data": {"user_email": null, "score": "test"}}',
            content_type="application/json",
            HTTP_EUPHROSYNE_CERTIFICATION=self.certification.name,
        )
        assert response.status_code == 400
        assert response.json() == {"error": "Score is required"}

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: True
    )
    @mock.patch("certification.providers.tally.hooks.TallyWebhookData.from_tally_data")
    def test_hook_when_score_is_zero(self, mock_from_tally_data: mock.MagicMock):
        mock_from_tally_data.return_value.user_email = StaffUserFactory().email
        mock_from_tally_data.return_value.score = 0
        response = self.client.post(
            "/certification/hooks/tally",
            data=b'{"data": {"user_email": null, "score": 0}}',
            content_type="application/json",
            HTTP_EUPHROSYNE_CERTIFICATION=self.certification.name,
        )
        assert response.status_code == 200

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: True
    )
    @mock.patch(
        "certification.providers.tally.hooks.create_quiz_result",
        mock.MagicMock(side_effect=Certification.DoesNotExist),
    )
    @mock.patch("certification.providers.tally.hooks.TallyWebhookData.from_tally_data")
    def test_hook_when_certification_do_not_exist(
        self, mock_from_tally_data: mock.MagicMock
    ):
        mock_from_tally_data.return_value.user_email = "email"
        mock_from_tally_data.return_value.score = 11.0
        response = self.client.post(
            "/certification/hooks/tally",
            data=b"{}",
            content_type="application/json",
            HTTP_EUPHROSYNE_CERTIFICATION=self.certification.name,
        )
        assert response.status_code == 400
        assert response.json() == {"error": "Certification not found"}

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: True
    )
    def test_tally_webhook_valid_when_passing_score(self):
        user = StaffUserFactory()
        success_score = PASSING_SCORE + 1
        response = self.client.post(
            "/certification/hooks/tally",
            data=json.dumps(get_tally_data(user.email, success_score)),
            content_type="application/json",
            headers={"Euphrosyne-Certification": self.certification.name},
        )

        assert response.status_code == 200

        quiz_result_qs = QuizResult.objects.filter(
            user=user, score=success_score, is_passed=True
        )
        assert quiz_result_qs.exists()
        assert CertificationNotification.objects.filter(
            user=user,
            certification=self.certification,
            type_of=NotificationType.SUCCESS,
            quiz_result=quiz_result_qs.first(),
        ).exists()

    @mock.patch(
        "certification.providers.tally.hooks._validate_signature", lambda _: True
    )
    def test_tally_webhook_valid_when_not_passing_score(self):
        user = StaffUserFactory()
        failed_score = PASSING_SCORE - 1
        response = self.client.post(
            "/certification/hooks/tally",
            data=json.dumps(get_tally_data(user.email, failed_score)),
            content_type="application/json",
            headers={"Euphrosyne-Certification": self.certification.name},
        )

        assert response.status_code == 200

        quiz_result_qs = QuizResult.objects.filter(
            user=user, score=failed_score, is_passed=False
        )
        assert quiz_result_qs.exists()
        assert not CertificationNotification.objects.filter(
            user=user,
            certification=self.certification,
            type_of=NotificationType.SUCCESS,
            quiz_result=quiz_result_qs.first(),
        ).exists()
