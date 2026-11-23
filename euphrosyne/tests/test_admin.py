from django.test import TestCase, override_settings
from django.urls import reverse


class TestAdmin(TestCase):
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
            f'<form action="{reverse("orcid_login")}" method="post">',
        )
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, '<button class="button" type="submit">')
        self.assertContains(response, "ORCID")

    def test_orcid_begin_does_not_redirect_on_get(self):
        response = self.client.get(reverse("orcid_login"))

        self.assertEqual(response.status_code, 200)

    @override_settings(
        SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    )
    def test_orcid_begin_post_redirects_to_orcid(self):
        response = self.client.post(reverse("orcid_login"), {"process": "login"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("https://orcid.org/oauth/authorize?"))
        self.assertNotIn("_session_expiry", self.client.session)
