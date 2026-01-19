from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class TestLowercaseEmailBackend(TestCase):
    def test_admin_login_lowercases_email(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            email="user@example.com", password="test-pass-123"
        )
        user.is_staff = True
        user.save()

        response = self.client.post(
            reverse("admin:login"),
            data={"username": "USER@EXAMPLE.COM", "password": "test-pass-123"},
            follow=True,
        )

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.pk, user.pk)
