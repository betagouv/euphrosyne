from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.test.testcases import TestCase
from django.urls import reverse
from django.utils import timezone

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


class TestUserCompleteAccountView(TestCase):
    def setUp(self) -> None:
        self.view_url = reverse(
            "complete_registration_orcid", kwargs={"token": "token"}
        )

    @patch.object(
        UserCompleteAccountView,
        "get_partial",
        new=MagicMock(return_value=PartialMock()),
    )
    def test_get_response_has_prefilled_inputs(self):
        response = self.client.get(self.view_url)
        content = str(response.content)
        assert (
            '<input type="text" name="first_name" value="John" maxlength="150" '
            'required id="id_first_name"'
        ) in content
        assert (
            '<input type="text" name="last_name" value="Doe" maxlength="150" '
            'required id="id_last_name"'
        ) in content

        assert (
            '<input type="email" name="email" value="test@test.test" maxlength="254" '
            'required id="id_email"'
        ) in content

    @patch.object(
        UserCompleteAccountView,
        "get_partial",
        new=MagicMock(return_value=PartialMock()),
    )
    def test_post_response_redirects(self):
        response = self.client.post(
            self.view_url,
            data={
                "email": "test@test.test",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("social:complete", args=("orcid",))

    @patch.object(
        UserCompleteAccountView,
        "get_partial",
        new=MagicMock(return_value=PartialMock()),
    )
    def test_view_set_additional_values(self):
        now = timezone.now()
        with patch("orcid_oauth.views.timezone") as timezone_mock:
            timezone_mock.now.return_value = now
            self.client.post(
                self.view_url,
                data={
                    "email": "test@test.test",
                    "first_name": "Jack",
                    "last_name": "Sparrow",
                },
            )

        user = User.objects.get(email="test@test.test")

        assert user.first_name == "Jack"
        assert user.last_name == "Sparrow"
        assert user.is_staff
        assert user.invitation_completed_at == now
