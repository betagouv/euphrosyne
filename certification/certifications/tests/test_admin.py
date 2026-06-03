import csv
import datetime
from io import StringIO

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory

from ..admin import CertificationAdmin
from ..models import Certification, QuizResult
from .factories import (
    CertificationOfTypeQuizFactory,
    QuizCertificationFactory,
    QuizResultFactory,
)


class CertificationAdminExportPassedUsersActionTests(TestCase):
    def setUp(self):
        self.model_admin = CertificationAdmin(Certification, AdminSite())
        self.request = RequestFactory().get(
            reverse("admin:certification_certification_changelist")
        )
        self.request.user = LabAdminUserFactory()

    def _export_rows(self, *certifications):
        response = self.model_admin.export_passed_users_as_csv(
            self.request,
            Certification.objects.filter(
                id__in=[certification.id for certification in certifications]
            ),
        )
        rows = list(csv.DictReader(StringIO(response.content.decode())))
        return response, rows

    @staticmethod
    def _set_created(result, created):
        QuizResult.objects.filter(id=result.id).update(created=created)
        result.refresh_from_db()

    def test_export_includes_passing_results_for_selected_certifications(self):
        certification = CertificationOfTypeQuizFactory(
            name="Laser safety", num_days_valid=10
        )
        quiz = QuizCertificationFactory(certification=certification, passing_score=80)
        quiz.url = "https://example.com/laser-safety"
        quiz.save()
        user = StaffUserFactory(
            first_name="Ada", last_name="Lovelace", email="ada@example.com"
        )
        passing_result = QuizResultFactory(
            user=user, quiz=quiz, score=80, is_passed=True
        )
        self._set_created(
            passing_result,
            datetime.datetime(2026, 1, 10, 12, tzinfo=datetime.timezone.utc),
        )

        under_threshold_user = StaffUserFactory(
            first_name="Grace", last_name="Hopper", email="grace@example.com"
        )
        QuizResultFactory(
            user=under_threshold_user, quiz=quiz, score=79, is_passed=False
        )

        certification_without_expiration = CertificationOfTypeQuizFactory(
            name="Data safety", num_days_valid=None
        )
        quiz_without_expiration = QuizCertificationFactory(
            certification=certification_without_expiration, passing_score=90
        )
        quiz_without_expiration.url = "https://example.com/data-safety"
        quiz_without_expiration.save()
        user_without_expiration = StaffUserFactory(
            first_name="Katherine",
            last_name="Johnson",
            email="katherine@example.com",
        )
        passing_without_expiration = QuizResultFactory(
            user=user_without_expiration,
            quiz=quiz_without_expiration,
            score=91,
            is_passed=True,
        )
        self._set_created(
            passing_without_expiration,
            datetime.datetime(2026, 2, 1, 12, tzinfo=datetime.timezone.utc),
        )

        response, rows = self._export_rows(
            certification, certification_without_expiration
        )

        assert response["Content-Type"] == "text/csv"
        self.assertRegex(
            response["Content-Disposition"],
            r'^attachment; filename="export-cert-selected-certifications-\d{8}-\d{6}\.csv"$',  # pylint: disable=line-too-long
        )
        assert response.content.decode().splitlines()[0] == (
            "certification,first_name,last_name,email,score,quiz_url,"
            "certificate_date,expiration_date"
        )
        assert rows == [
            {
                "certification": "Laser safety",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "score": "80.0",
                "quiz_url": "https://example.com/laser-safety",
                "certificate_date": "2026-01-10",
                "expiration_date": "2026-01-20",
            },
            {
                "certification": "Data safety",
                "first_name": "Katherine",
                "last_name": "Johnson",
                "email": "katherine@example.com",
                "score": "91.0",
                "quiz_url": "https://example.com/data-safety",
                "certificate_date": "2026-02-01",
                "expiration_date": "",
            },
        ]

    def test_export_keeps_latest_passing_result_per_user_and_certification(self):
        certification = CertificationOfTypeQuizFactory(
            name="Radiation safety", num_days_valid=30
        )
        quiz = QuizCertificationFactory(certification=certification, passing_score=70)
        quiz.url = "https://example.com/radiation-safety"
        quiz.save()
        user = StaffUserFactory(
            first_name="Marie", last_name="Curie", email="marie@example.com"
        )
        older_result = QuizResultFactory(user=user, quiz=quiz, score=95, is_passed=True)
        self._set_created(
            older_result,
            datetime.datetime(2026, 3, 1, 12, tzinfo=datetime.timezone.utc),
        )
        latest_result = QuizResultFactory(
            user=user, quiz=quiz, score=75, is_passed=True
        )
        self._set_created(
            latest_result,
            datetime.datetime(2026, 3, 5, 12, tzinfo=datetime.timezone.utc),
        )

        response, rows = self._export_rows(certification)

        self.assertRegex(
            response["Content-Disposition"],
            r'^attachment; filename="export-cert-radiation-safety-\d{8}-\d{6}\.csv"$',
        )
        assert rows == [
            {
                "certification": "Radiation safety",
                "first_name": "Marie",
                "last_name": "Curie",
                "email": "marie@example.com",
                "score": "75.0",
                "quiz_url": "https://example.com/radiation-safety",
                "certificate_date": "2026-03-05",
                "expiration_date": "2026-04-04",
            }
        ]
