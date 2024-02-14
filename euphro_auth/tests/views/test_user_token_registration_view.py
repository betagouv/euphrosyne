from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class TestUserTokenRegistrationView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create(email="test@test.test")
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
        print(response.content)
        self.assertContains(
            response,
            (
                '<input type="email" name="email" value="test@test.test" '
                'autocomplete="email" maxlength="254" required id="id_email"'
            ),
        )

    def test_user_logged_in_on_success(self):
        preresponse = self.client.get(self.view_url)
        self.client.post(
            preresponse.headers["Location"],
            data={
                "email": "test@test.test",
                "new_password1": "NewPassword@1",
                "new_password2": "NewPassword@1",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_orcid_registration_link_is_valid(self):
        preresponse = self.client.get(self.view_url)
        response = self.client.get(preresponse.headers["Location"])
        self.assertContains(
            response,
            f'href="{reverse("social:begin", args=("orcid",))}?user_id={self.user.pk}"',
        )
