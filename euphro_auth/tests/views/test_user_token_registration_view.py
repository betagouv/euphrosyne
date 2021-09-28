from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from euphro_auth.models import User

from ...views import UserTokenRegistrationView


class TestUserTokenRegistrationView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(email="test@test.test")
        self.view_url = reverse(
            "registration_token",
            args=[
                urlsafe_base64_encode(force_bytes(self.user.pk)),
                default_token_generator.make_token(self.user),
            ],
        )

    def test_email_should_be_prefilled(self):
        preresponse = self.client.get(self.view_url)
        response = self.client.get(preresponse.headers["Location"])
        self.assertContains(
            response,
            (
                '<input type="email" name="email" value="test@test.test" '
                'autocomplete="email" maxlength="254" required id="id_email">'
            ),
        )

    def test_user_can_set_password(self):
        response = self.client.get(self.view_url)
        self.client.post(
            response.headers["Location"],
            data={
                "new_password1": "securepassword",
                "new_password2": "securepassword",
                "email": "test@test.test",
            },
        )
        self.assertTrue(
            check_password(
                "securepassword", User.objects.get(email="test@test.test").password
            )
        )

    def test_user_can_change_email(self):
        response = self.client.get(self.view_url)
        self.client.post(
            response.headers["Location"],
            data={
                "new_password1": "securepassword",
                "new_password2": "securepassword",
                "email": "anotheremail@test.test",
            },
        )
        self.assertEqual(
            User.objects.get(id=self.user.id).email, "anotheremail@test.test"
        )
