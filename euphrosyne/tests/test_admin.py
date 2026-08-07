from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class TestAdmin(SimpleTestCase):
    @override_settings(
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
    )
    def test_admin_login_has_orcid_post_form(self):
        response = self.client.get(reverse("admin:login"))
        self.assertContains(
            response,
            f'<form action="{reverse("social:begin", args=("orcid",))}" method="post">',
        )
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, '<button class="button" type="submit">')
        self.assertContains(response, "ORCID")

    def test_orcid_begin_rejects_get(self):
        response = self.client.get(reverse("social:begin", args=("orcid",)))

        self.assertEqual(response.status_code, 405)

    @override_settings(
        SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
        SOCIAL_AUTH_ORCID_KEY="client-id",
        SOCIAL_AUTH_ORCID_SECRET="client-secret",
    )
    def test_orcid_begin_post_redirects_to_orcid(self):
        response = self.client.post(reverse("social:begin", args=("orcid",)))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("https://orcid.org/oauth/authorize?"))
