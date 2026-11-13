from http import HTTPStatus
from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount
from django.contrib import auth
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from euphro_auth.models import User

from ...completion import COMPLETION_SESSION_KEY


class TestUserCompleteAccountView(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.test")
        account = SocialAccount.objects.create(
            user=self.user, provider="orcid", uid="0000-0001-2345-6789"
        )
        session = self.client.session
        session[COMPLETION_SESSION_KEY] = {
            "token": "completion-token",
            "user_id": self.user.pk,
            "account_id": account.pk,
            "details": {
                "email": "test@test.test",
                "first_name": "John",
                "last_name": "Doe",
            },
            "created_at": int(timezone.now().timestamp()),
        }
        session.save()
        self.view_url = reverse(
            "complete_registration_orcid", kwargs={"token": "completion-token"}
        )

    def test_get_response_has_prefilled_inputs(self):
        response = self.client.get(self.view_url)
        self.assertContains(response, 'name="first_name" value="John"')
        self.assertContains(response, 'name="last_name" value="Doe"')
        self.assertContains(response, 'name="email" value="test@test.test"')

    def test_post_signs_in_and_redirects(self):
        response = self.client.post(
            self.view_url,
            data={"email": "test@test.test", "first_name": "John", "last_name": "Doe"},
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, "/")
        self.assertEqual(auth.get_user(self.client).pk, self.user.pk)

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
