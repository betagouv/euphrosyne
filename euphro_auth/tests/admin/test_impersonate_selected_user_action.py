from unittest import mock

from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import gettext

from euphro_auth.models import User
from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory

from ...admin import UserAdmin


class MockedMessages(list):
    def add(self, level, message, extra_tags=None, fail_silently=False):
        self.append((level, message, extra_tags, fail_silently))


class TestImpersonateSelectedUserAction(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.model_admin = UserAdmin(User, AdminSite())

    def get_request(self, user):
        request = self.request_factory.post(
            reverse("admin:euphro_auth_user_changelist"),
            REMOTE_ADDR="203.0.113.10",
        )
        request.user = user
        request._messages = MockedMessages()  # pylint: disable=protected-access
        return request

    def get_request_with_session(self, user):
        request = self.get_request(user)
        middleware = SessionMiddleware(lambda request: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_impersonation_action_is_only_visible_to_superusers(self):
        non_superuser_request = self.get_request(LabAdminUserFactory())
        superuser_request = self.get_request(LabAdminUserFactory(is_superuser=True))

        non_superuser_actions = self.model_admin.get_actions(non_superuser_request)
        superuser_actions = self.model_admin.get_actions(superuser_request)

        assert "impersonate_selected_user" not in non_superuser_actions
        assert "impersonate_selected_user" in superuser_actions

    def test_impersonation_action_rejects_non_superusers_server_side(self):
        request = self.get_request(LabAdminUserFactory())
        target_user = StaffUserFactory()

        response = self.model_admin.impersonate_selected_user(
            request,
            User.objects.filter(pk=target_user.pk),
        )

        assert response is None
        assert request._messages == [  # pylint: disable=protected-access
            (
                messages.ERROR,
                gettext("You do not have permission to impersonate users."),
                "",
                False,
            )
        ]

    def test_impersonation_action_requires_exactly_one_user(self):
        request = self.get_request(LabAdminUserFactory(is_superuser=True))
        StaffUserFactory()
        StaffUserFactory()

        response = self.model_admin.impersonate_selected_user(
            request,
            User.objects.all(),
        )

        assert response is None
        assert request._messages == [  # pylint: disable=protected-access
            (
                messages.ERROR,
                gettext("Please select exactly one user to impersonate."),
                "",
                False,
            )
        ]

    def test_impersonation_action_rejects_superuser_target(self):
        request = self.get_request(LabAdminUserFactory(is_superuser=True))
        target_user = StaffUserFactory(is_superuser=True)

        response = self.model_admin.impersonate_selected_user(
            request,
            User.objects.filter(pk=target_user.pk),
        )

        assert response is None
        assert request._messages == [  # pylint: disable=protected-access
            (
                messages.ERROR,
                gettext("Impersonating superusers is not allowed."),
                "",
                False,
            )
        ]

    def test_impersonation_action_logs_in_target_user_and_stores_metadata(self):
        admin_user = LabAdminUserFactory(is_superuser=True)
        target_user = StaffUserFactory(email="target@example.com")
        request = self.get_request_with_session(admin_user)

        with mock.patch("euphro_auth.admin.logger.warning") as log_warning:
            response = self.model_admin.impersonate_selected_user(
                request,
                User.objects.filter(pk=target_user.pk),
            )

        assert response.status_code == 302
        assert response.headers["Location"] == "/"
        assert int(request.session["_auth_user_id"]) == target_user.pk
        assert request.session["_auth_user_backend"] == (
            "orcid_oauth.backends.ORCIDOAuth2"
        )
        assert request.session["impersonator_user_id"] == admin_user.pk
        assert request.session["impersonated_user_id"] == target_user.pk
        assert request.session["impersonation_started_at"]
        assert request.user == target_user
        assert request._messages == [  # pylint: disable=protected-access
            (
                messages.SUCCESS,
                gettext("You are now impersonating {}.").format(target_user),
                "",
                False,
            )
        ]
        log_warning.assert_called_once()
        assert log_warning.call_args.args == ("Starting user impersonation",)
        assert log_warning.call_args.kwargs["extra"] == {
            "impersonator_user_id": admin_user.pk,
            "impersonated_user_id": target_user.pk,
            "impersonation_started_at": request.session["impersonation_started_at"],
            "remote_addr": "203.0.113.10",
        }
