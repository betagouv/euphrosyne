from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class TestPasswordLogin(TestCase):
    def test_login_lowercases_email(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            email="user@example.com", password="T8!vQ2#rM6@zL9$p"
        )
        user.is_staff = True
        user.save()

        response = self.client.post(
            reverse("account_login"),
            data={"login": "USER@EXAMPLE.COM", "password": "T8!vQ2#rM6@zL9$p"},
            follow=True,
        )

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.pk, user.pk)

    def test_admin_login_url_serves_the_sign_in_page(self):
        response = self.client.get(reverse("admin:login"), {"next": "/lab/project/"})

        self.assertContains(response, 'id="login-form"')
        self.assertContains(response, reverse("account_reset_password"), count=1)
        self.assertContains(response, 'name="next" value="/lab/project/"')
