from django.test import SimpleTestCase
from django.urls import reverse


class TestAdmin(SimpleTestCase):
    def test_admin_login_has_orcid_url(self):
        response = self.client.get(reverse("admin:login"))
        self.assertContains(
            response, f'href="{reverse("social:begin", args=("orcid",))}"'
        )
