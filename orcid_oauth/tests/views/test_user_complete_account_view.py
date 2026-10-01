from http import HTTPStatus
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from social_core.utils import PARTIAL_TOKEN_SESSION_NAME
from social_django.models import Partial, UserSocialAuth

from euphro_auth.models import User


class TestUserCompleteAccountView(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.test")
        social = UserSocialAuth.objects.create(
            user=self.user, provider="orcid", uid="0000-0001-2345-6789"
        )
        partial = Partial.prepare(
            "orcid",
            settings.SOCIAL_AUTH_PIPELINE.index(
                "orcid_oauth.pipeline.complete_information"
            ),
            {
                "args": [],
                "kwargs": {
                    "user": self.user.pk,
                    "social": {"provider": "orcid", "uid": social.uid},
                    "uid": social.uid,
                    "details": {"first_name": "John", "last_name": "Doe"},
                },
            },
        )
        partial.save()
        self.view_url = reverse(
            "complete_registration_orcid", kwargs={"token": partial.token}
        )
        session = self.client.session
        session[PARTIAL_TOKEN_SESSION_NAME] = partial.token
        session.save()

    def test_get_response_has_prefilled_inputs(self):
        response = self.client.get(self.view_url)
        self.assertContains(response, 'name="first_name" value="John"')
        self.assertContains(response, 'name="last_name" value="Doe"')
        self.assertContains(response, 'name="email" value="test@test.test"')

    def test_post_response_redirects(self):
        response = self.client.post(
            self.view_url,
            data={"email": "test@test.test", "first_name": "John", "last_name": "Doe"},
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("social:complete", args=("orcid",)))

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
