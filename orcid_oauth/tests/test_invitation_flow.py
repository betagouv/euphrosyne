from copy import deepcopy
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib import auth
from django.contrib.auth.tokens import default_token_generator
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from social_core.utils import PARTIAL_TOKEN_SESSION_NAME
from social_django.models import UserSocialAuth

from euphro_auth.models import User

from ..backends import ORCIDOAuth2
from ..invitations import (
    CONTEXT_MAX_AGE,
    INVITATION_SESSION_KEY,
    REGISTRATION_SESSION_KEY,
)


@override_settings(
    SOCIAL_AUTH_ORCID_KEY="client-id",
    SOCIAL_AUTH_ORCID_SECRET="client-secret",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    },
)
class TestORCIDInvitationFlow(TestCase):  # pylint: disable=too-many-public-methods
    def setUp(self) -> None:
        self.victim = User.objects.create(
            pk=1, email="victim@example.com", first_name="Victim", last_name="Account"
        )
        self.invited = User.objects.create(pk=2, email="invited@example.com")
        self.begin_url = reverse("social:begin", args=("orcid",))
        self.register_url = reverse("begin_registration_orcid")
        self.callback_url = reverse("social:complete", args=("orcid",))

    def invitation_url(self, user: User, token: str | None = None) -> str:
        return reverse(
            "registration_token",
            args=(
                urlsafe_base64_encode(force_bytes(user.pk)),
                token or default_token_generator.make_token(user),
            ),
        )

    def validate_invitation(self, user: User | None = None) -> None:
        response = self.client.get(self.invitation_url(user or self.invited))
        self.assertEqual(response.status_code, 302)
        self.assertIn(INVITATION_SESSION_KEY, self.client.session)

    def callback(self, uid: str = "0000-0002-1234-5678", *, data: dict | None = None):
        # Only remote ORCID responses are mocked. OAuth state validation, the
        # actual pipeline, associations and Django authentication all run.
        profile = {
            "orcid-identifier": {"path": uid},
            "person": {
                "name": {
                    "given-names": {"value": "ORCID"},
                    "family-name": {"value": "User"},
                },
                "emails": {"email": []},
            },
        }
        with (
            patch.object(
                ORCIDOAuth2,
                "request_access_token",
                return_value={
                    "orcid": uid,
                    "access_token": "test-access-token",
                    "token_type": "bearer",
                },
            ),
            patch.object(ORCIDOAuth2, "user_data", return_value=profile),
        ):
            return self.client.get(
                self.callback_url,
                {
                    "state": self.client.session["orcid_state"],
                    "code": "valid-test-code",
                    **(data or {}),
                },
            )

    def assert_no_association(self) -> None:
        self.assertFalse(UserSocialAuth.objects.exists())
        self.assertFalse(auth.get_user(self.client).is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(User.objects.count(), 2)
        self.victim.refresh_from_db()
        self.assertEqual(self.victim.first_name, "Victim")

    def test_incident_post_user_id_one_and_valid_attacker_callback(self):
        response = self.client.post(self.begin_url, {"user_id": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("user_id", self.client.session)
        response = self.callback(data={"user_id": "1"})
        self.assertEqual(response.url, reverse("admin:login"))
        self.assert_no_association()

    def test_query_string_user_id_is_ignored(self):
        self.assertEqual(
            self.client.get(f"{self.begin_url}?user_id=1").status_code, 405
        )
        self.client.post(f"{self.begin_url}?user_id=1")
        self.callback(data={"user_id": "1", "uid": "1", "email": self.victim.email})
        self.assert_no_association()

    def test_legacy_generic_session_user_id_is_ignored(self):
        session = self.client.session
        session["user_id"] = self.victim.pk
        session.save()
        self.client.post(self.begin_url)
        self.callback()
        self.assert_no_association()

    def test_unknown_orcid_without_invitation_cannot_create_account(self):
        self.client.post(self.begin_url)
        self.callback()
        self.assert_no_association()

    def test_registration_start_requires_valid_context(self):
        response = self.client.post(self.register_url, {"user_id": "1"})
        self.assertEqual(response.url, reverse("admin:login"))
        self.assert_no_association()
        self.assertEqual(self.client.get(self.register_url).status_code, 405)

    def test_unknown_orcid_cannot_associate_authenticated_browser_user(self):
        self.client.force_login(self.victim)
        self.client.post(self.begin_url, {"user_id": "1"})
        self.callback()
        self.assertFalse(UserSocialAuth.objects.exists())
        self.victim.refresh_from_db()
        self.assertEqual(self.victim.first_name, "Victim")

    def test_invalid_expired_and_other_users_tokens_clear_context(self):
        with patch.object(
            default_token_generator,
            "_now",
            return_value=datetime.now() - timedelta(days=4),
        ):
            expired_token = default_token_generator.make_token(self.invited)
        urls = (
            self.invitation_url(self.invited, "invalid-token"),
            self.invitation_url(self.invited, expired_token),
            self.invitation_url(
                self.invited, default_token_generator.make_token(self.victim)
            ),
            reverse("registration_token", args=("invalid-uid", "invalid-token")),
        )
        for index, url in enumerate(urls):
            with self.subTest(case=index):
                self.validate_invitation()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
                self.client.post(self.begin_url, {"user_id": "1"})
                self.callback()
                self.assert_no_association()

    def test_valid_invitation_rotates_session_and_selects_only_its_target(self):
        original_key = self.client.session.session_key
        self.validate_invitation()
        self.assertNotEqual(self.client.session.session_key, original_key)
        self.client.post(self.register_url)
        response = self.callback()
        self.assertIn("/registration/orcid/verify/", response.url)
        self.assertEqual(UserSocialAuth.objects.get().user_id, self.invited.pk)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_form_and_callback_identifiers_cannot_change_validated_target(self):
        self.validate_invitation()
        forged = {"user_id": "1", "uid": "1", "email": self.victim.email}
        self.client.post(f"{self.register_url}?user_id=1", forged)
        self.callback(data=forged)
        self.assertEqual(UserSocialAuth.objects.get().user_id, self.invited.pk)
        self.assertFalse(UserSocialAuth.objects.filter(user=self.victim).exists())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_expired_or_inconsistent_context_is_cleared_at_start(self):
        for changes in (
            {"validated_at": int(timezone.now().timestamp()) - CONTEXT_MAX_AGE},
            {"validated_at": int(timezone.now().timestamp()) + 60},
            {"session_key": "another-session"},
            {"user_id": 999999},
            {"token": "invalid-token"},
        ):
            with self.subTest(changes=tuple(changes)):
                self.validate_invitation()
                session = self.client.session
                session[INVITATION_SESSION_KEY] = {
                    **session[INVITATION_SESSION_KEY],
                    **changes,
                }
                session.save()
                response = self.client.post(self.register_url)
                self.assertEqual(response.url, reverse("admin:login"))
                self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
                self.assert_no_association()

    def test_context_is_rechecked_at_callback(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        session = self.client.session
        session[INVITATION_SESSION_KEY] = {
            **session[INVITATION_SESSION_KEY],
            "validated_at": int(timezone.now().timestamp()) - CONTEXT_MAX_AGE,
        }
        session.save()
        response = self.callback()
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assert_no_association()

    def test_invitation_context_cannot_be_transferred_to_another_session(self):
        self.validate_invitation()
        other_client = Client()
        session = other_client.session
        session[INVITATION_SESSION_KEY] = deepcopy(
            self.client.session[INVITATION_SESSION_KEY]
        )
        session.save()
        response = other_client.post(self.register_url)
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn(INVITATION_SESSION_KEY, other_client.session)
        self.assert_no_association()

    def test_context_is_single_use_even_with_an_old_session_snapshot(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        old_context = deepcopy(self.client.session[INVITATION_SESSION_KEY])
        self.callback()
        session = self.client.session
        session[INVITATION_SESSION_KEY] = old_context
        session.save()
        response = self.client.post(self.register_url)
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.client.post(self.begin_url)
        self.callback(uid="0000-0009-9999-9999")
        self.assertEqual(UserSocialAuth.objects.count(), 1)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_completed_invitation_cannot_authorize_association(self):
        url = self.invitation_url(self.invited)
        self.invited.invitation_completed_at = timezone.now()
        self.invited.save()
        self.client.get(url)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.client.post(self.begin_url)
        self.callback()
        self.assert_no_association()

    def test_invitation_completed_during_oauth_is_rejected(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        self.invited.invitation_completed_at = timezone.now()
        self.invited.save()
        self.callback()
        self.assert_no_association()

    def test_changed_invitation_token_during_oauth_is_rejected(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        self.invited.set_password("changed-password")
        self.invited.save()
        self.callback()
        self.assert_no_association()

    def test_opening_another_link_during_oauth_cannot_change_target(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        self.validate_invitation(self.victim)
        self.callback()
        self.assert_no_association()

    def test_orcid_associated_with_another_account_cannot_use_invitation(self):
        UserSocialAuth.objects.create(
            user=self.victim, provider="orcid", uid="0000-0002-1234-5678"
        )
        self.validate_invitation()
        self.client.post(self.register_url)
        response = self.callback()
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertEqual(UserSocialAuth.objects.get().user_id, self.victim.pk)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_existing_orcid_login_still_works_with_forged_identifiers(self):
        self.invited.invitation_completed_at = timezone.now()
        self.invited.save()
        UserSocialAuth.objects.create(
            user=self.invited, provider="orcid", uid="0000-0002-1234-5678"
        )
        session = self.client.session
        session["user_id"] = self.victim.pk
        session.save()
        self.client.post(self.begin_url, {"user_id": "1"})
        self.callback(data={"user_id": "1"})
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)
        self.assertEqual(UserSocialAuth.objects.count(), 1)

    def test_registration_completion_and_callback_authenticate_only_invited_user(self):
        self.validate_invitation()
        self.client.post(self.register_url, {"user_id": "1"})
        completion_url = self.callback().url
        self.assertEqual(self.client.get(completion_url).status_code, 200)
        self.client.post(
            completion_url,
            {
                "email": self.invited.email,
                "first_name": "Invited",
                "last_name": "User",
                "user_id": "1",
            },
        )
        self.client.get(self.callback_url)
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertNotIn(REGISTRATION_SESSION_KEY, self.client.session)
        self.assertNotIn(PARTIAL_TOKEN_SESSION_NAME, self.client.session)
        self.assertEqual(self.client.post(completion_url).url, reverse("admin:login"))

    def test_partial_form_cannot_be_used_in_another_session(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        completion_url = self.callback().url
        other_client = Client()
        response = other_client.post(
            completion_url,
            {
                "email": "stolen@example.com",
                "first_name": "Stolen",
                "last_name": "Account",
            },
        )
        self.assertEqual(response.url, reverse("admin:login"))
        self.invited.refresh_from_db()
        self.assertEqual(self.invited.email, "invited@example.com")
        self.assertIsNone(self.invited.invitation_completed_at)

    def test_copied_registration_context_cannot_cross_sessions(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        completion_url = self.callback().url
        other_client = Client()
        session = other_client.session
        for key in (REGISTRATION_SESSION_KEY, PARTIAL_TOKEN_SESSION_NAME):
            session[key] = deepcopy(self.client.session[key])
        session.save()
        self.assertEqual(other_client.get(completion_url).url, reverse("admin:login"))
        self.assertNotIn(REGISTRATION_SESSION_KEY, other_client.session)

    def test_expired_registration_continuation_cannot_modify_account(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        completion_url = self.callback().url
        session = self.client.session
        session[REGISTRATION_SESSION_KEY] = {
            **session[REGISTRATION_SESSION_KEY],
            "validated_at": int(timezone.now().timestamp()) - CONTEXT_MAX_AGE,
        }
        session.save()
        response = self.client.post(
            completion_url,
            {
                "email": "expired@example.com",
                "first_name": "Expired",
                "last_name": "User",
            },
        )
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn(REGISTRATION_SESSION_KEY, self.client.session)
        self.invited.refresh_from_db()
        self.assertEqual(self.invited.email, "invited@example.com")
        self.assertIsNone(self.invited.invitation_completed_at)

    def test_deleted_target_during_oauth_is_rejected(self):
        self.validate_invitation()
        self.client.post(self.register_url)
        User.objects.filter(pk=self.invited.pk).delete()
        response = self.callback()
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertFalse(UserSocialAuth.objects.exists())
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_classic_registration_still_completes_and_logs_in(self):
        response = self.client.get(self.invitation_url(self.invited))
        self.client.post(
            response.url,
            {
                "email": self.invited.email,
                "first_name": "Classic",
                "last_name": "User",
                "new_password1": "NewPassword@1",
                "new_password2": "NewPassword@1",
            },
        )
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)
        self.invited.refresh_from_db()
        self.assertIsNotNone(self.invited.invitation_completed_at)
        self.assertTrue(self.invited.check_password("NewPassword@1"))
        self.assertFalse(UserSocialAuth.objects.exists())
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
