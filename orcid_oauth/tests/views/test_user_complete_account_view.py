from http import HTTPStatus
from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from euphro_auth.models import User

from ..helpers import orcid_record


class TestUserCompleteAccountView(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.test")
        SocialAccount.objects.create(
            user=self.user,
            provider="orcid",
            uid="0000-0001-2345-6789",
            extra_data=orcid_record(
                "0000-0001-2345-6789", first_name="John", last_name="Doe"
            ),
        )
        self.client.force_login(self.user)
        self.view_url = reverse("complete_registration_orcid")

    def test_get_response_has_prefilled_inputs(self):
        response = self.client.get(self.view_url)
        self.assertContains(response, 'name="first_name" value="John"')
        self.assertContains(response, 'name="last_name" value="Doe"')
        self.assertContains(response, 'name="email" value="test@test.test"')

    def test_post_redirects(self):
        response = self.client.post(
            self.view_url,
            data={"email": "test@test.test", "first_name": "John", "last_name": "Doe"},
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, "/")

    def test_view_set_additional_values(self):
        now = timezone.now()
        with patch("orcid_oauth.views.timezone.now", return_value=now):
            self.client.post(
                self.view_url,
                data={
                    "email": "test@test.test",
                    "first_name": "Jack",
                    "last_name": "Sparrow",
                },
            )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jack")
        self.assertEqual(self.user.last_name, "Sparrow")
        self.assertTrue(self.user.is_staff)
        self.assertEqual(self.user.invitation_completed_at, now)

    def test_completed_account_is_sent_home(self):
        self.user.invitation_completed_at = timezone.now()
        self.user.save()
        self.assertEqual(self.client.get(self.view_url).url, "/")

    def test_api_calls_get_the_gate_as_json(self):
        response = self.client.get("/api/auth/token/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json()["code"], "account_completion_required")
        self.assertEqual(response.json()["redirect_url"], self.view_url)
