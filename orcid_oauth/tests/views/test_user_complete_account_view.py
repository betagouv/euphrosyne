from http import HTTPStatus
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse

from euphro_auth.models import User

from ...views import UserCompleteAccountView


class PartialMock:
    kwargs = {
        "user": User(
            id=1,
            email="test@test.test",
        ),
        "details": {
            "first_name": "John",
            "last_name": "Doe",
        },
    }
    backend = "orcid"


class FormMock:
    @staticmethod
    def save():
        return {}

    @staticmethod
    def is_valid():
        return True


class TestUserCompleteAccountView(SimpleTestCase):
    def setUp(self) -> None:
        self.view_url = reverse(
            "complete_registration_orcid", kwargs={"token": "token"}
        )

    def test_get_response_has_prefilled_inputs(self):
        with patch.object(
            UserCompleteAccountView,
            "get_partial",
            return_value=PartialMock(),
        ):
            response = self.client.get(self.view_url)
        content = str(response.content)
        assert (
            '<input type="text" name="first_name" value="John" maxlength="150" '
            'required id="id_first_name">'
        ) in content
        assert (
            '<input type="text" name="last_name" value="Doe" maxlength="150" '
            'required id="id_last_name">'
        ) in content

        assert (
            '<input type="email" name="email" value="test@test.test" maxlength="254" '
            'required id="id_email">'
        ) in content

    def test_post_response_redirects(self):
        with patch.object(
            UserCompleteAccountView,
            "get_partial",
            return_value=PartialMock(),
        ):
            with patch.object(
                UserCompleteAccountView,
                "get_form",
                return_value=FormMock(),
            ):
                response = self.client.post(
                    self.view_url,
                    data={
                        "email": "test@test.test",
                        "fist_name": "John",
                        "last_name": "Doe",
                    },
                )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("social:complete", args=("orcid",))
