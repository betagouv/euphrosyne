from copy import deepcopy
from datetime import datetime, timedelta
from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount
from django.contrib import auth
from django.contrib.auth.tokens import default_token_generator
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from euphro_auth.models import User

from ..completion import COMPLETION_MAX_AGE, COMPLETION_SESSION_KEY
from ..invitations import CONTEXT_MAX_AGE, INVITATION_SESSION_KEY
from .helpers import (
    DEFAULT_UID,
    STATES_SESSION_KEY,
    latest_oauth_state,
    orcid_callback,
    start_orcid_login,
)

OAUTH_STATES_SESSION_KEY = STATES_SESSION_KEY


@override_settings(
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
        self.begin_url = reverse("orcid_login")
        self.register_url = reverse(
            "registration_token",
            args=(urlsafe_base64_encode(force_bytes(self.invited.pk)), "registration"),
        )
        self.callback_url = reverse("orcid_callback")

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
        self.register_url = response.headers["Location"]

    def oauth_state(self) -> str:
        return latest_oauth_state(self.client)

    def start_registration(self, data: dict | None = None):
        return self.client.post(
            self.register_url, {"provider": "orcid", **(data or {})}
        )

    def begin(self, data: dict | None = None, query: str = ""):
        return start_orcid_login(self.client, data, query)

    def callback(self, uid: str = DEFAULT_UID, *, data: dict | None = None):
        # Only remote ORCID responses are mocked. OAuth state validation, the
        # adapter, associations and Django authentication all run.
        return orcid_callback(self.client, uid, data=data)

    def assert_no_association(self) -> None:
        self.assertFalse(SocialAccount.objects.exists())
        self.assertFalse(auth.get_user(self.client).is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(User.objects.count(), 2)
        self.victim.refresh_from_db()
        self.assertEqual(self.victim.first_name, "Victim")

    def test_incident_post_user_id_one_and_valid_attacker_callback(self):
        response = self.begin({"user_id": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("user_id", self.client.session)
        response = self.callback(data={"user_id": "1"})
        self.assertEqual(response.url, reverse("admin:login"))
        self.assert_no_association()

    def test_query_string_user_id_is_ignored(self):
        # A GET only shows a confirmation page: no OAuth attempt starts.
        self.assertEqual(
            self.client.get(f"{self.begin_url}?user_id=1").status_code, 200
        )
        self.assertNotIn(OAUTH_STATES_SESSION_KEY, self.client.session)
        self.begin(query="?user_id=1")
        self.callback(data={"user_id": "1", "uid": "1", "email": self.victim.email})
        self.assert_no_association()

    def test_legacy_generic_session_user_id_is_ignored(self):
        session = self.client.session
        session["user_id"] = self.victim.pk
        session.save()
        self.begin()
        self.callback()
        self.assert_no_association()

    def test_unknown_orcid_without_invitation_cannot_create_account(self):
        self.begin()
        self.callback()
        self.assert_no_association()

    def test_registration_start_requires_valid_context(self):
        self.validate_invitation()
        session = self.client.session
        session.pop(INVITATION_SESSION_KEY)
        session.save()
        response = self.start_registration({"user_id": "1"})
        self.assertEqual(response.url, reverse("admin:login"))
        self.assert_no_association()
        self.assertEqual(
            self.client.get(self.register_url, {"provider": "orcid"}).status_code, 200
        )
        self.assertNotIn(OAUTH_STATES_SESSION_KEY, self.client.session)

    def test_orcid_post_without_a_validated_invitation_link_is_rejected(self):
        response = self.start_registration({"user_id": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["validlink"])
        self.assertNotIn(OAUTH_STATES_SESSION_KEY, self.client.session)
        self.assert_no_association()

    def test_orcid_post_cannot_change_the_invitation_page_uid(self):
        self.validate_invitation()
        other_page = reverse(
            "registration_token",
            args=(urlsafe_base64_encode(force_bytes(self.victim.pk)), "registration"),
        )
        response = self.client.post(other_page, {"provider": "orcid"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertNotIn(OAUTH_STATES_SESSION_KEY, self.client.session)
        self.assert_no_association()

    def test_orcid_post_requires_the_invitation_forms_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        page = client.get(self.invitation_url(self.invited)).url
        client.get(page)
        response = client.post(page, {"provider": "orcid"})
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(OAUTH_STATES_SESSION_KEY, client.session)
        self.assertFalse(SocialAccount.objects.exists())

    def test_unknown_orcid_cannot_associate_authenticated_browser_user(self):
        self.client.force_login(self.victim)
        self.begin({"user_id": "1"})
        self.callback()
        self.assertFalse(SocialAccount.objects.exists())
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
                self.begin({"user_id": "1"})
                self.callback()
                self.assert_no_association()

    def test_valid_invitation_rotates_session_and_selects_only_its_target(self):
        original_key = self.client.session.session_key
        self.validate_invitation()
        self.assertNotEqual(self.client.session.session_key, original_key)
        self.start_registration()
        response = self.callback()
        self.assertIn("/registration/orcid/verify/", response.url)
        self.assertEqual(SocialAccount.objects.get().user_id, self.invited.pk)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_form_and_callback_identifiers_cannot_change_validated_target(self):
        self.validate_invitation()
        forged = {"user_id": "1", "uid": "1", "email": self.victim.email}
        self.client.post(
            f"{self.register_url}?user_id=1", {"provider": "orcid", **forged}
        )
        self.callback(data=forged)
        self.assertEqual(SocialAccount.objects.get().user_id, self.invited.pk)
        self.assertFalse(SocialAccount.objects.filter(user=self.victim).exists())
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
                response = self.start_registration()
                self.assertEqual(response.url, reverse("admin:login"))
                self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
                self.assert_no_association()

    def test_context_is_rechecked_at_callback(self):
        self.validate_invitation()
        self.start_registration()
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
        other_client.get(self.invitation_url(self.invited))
        session = other_client.session
        session[INVITATION_SESSION_KEY] = deepcopy(
            self.client.session[INVITATION_SESSION_KEY]
        )
        session.save()
        response = other_client.post(self.register_url, {"provider": "orcid"})
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn(INVITATION_SESSION_KEY, other_client.session)
        self.assert_no_association()

    def test_context_is_single_use_even_with_an_old_session_snapshot(self):
        self.validate_invitation()
        self.start_registration()
        old_context = deepcopy(self.client.session[INVITATION_SESSION_KEY])
        self.callback()
        session = self.client.session
        session[INVITATION_SESSION_KEY] = old_context
        session.save()
        response = self.start_registration()
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.begin()
        self.callback(uid="0000-0009-9999-9999")
        self.assertEqual(SocialAccount.objects.count(), 1)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_completed_invitation_cannot_authorize_association(self):
        url = self.invitation_url(self.invited)
        self.invited.invitation_completed_at = timezone.now()
        self.invited.save()
        self.client.get(url)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.begin()
        self.callback()
        self.assert_no_association()

    def test_invitation_completed_during_oauth_is_rejected(self):
        self.validate_invitation()
        self.start_registration()
        self.invited.invitation_completed_at = timezone.now()
        self.invited.save()
        self.callback()
        self.assert_no_association()

    def test_changed_invitation_token_during_oauth_is_rejected(self):
        self.validate_invitation()
        self.start_registration()
        self.invited.set_password("changed-password")
        self.invited.save()
        self.callback()
        self.assert_no_association()

    def test_opening_another_link_during_oauth_cannot_change_target(self):
        self.validate_invitation()
        self.start_registration()
        self.validate_invitation(self.victim)
        self.callback()
        self.assert_no_association()

    def test_orcid_associated_with_another_account_cannot_use_invitation(self):
        SocialAccount.objects.create(
            user=self.victim, provider="orcid", uid="0000-0002-1234-5678"
        )
        self.validate_invitation()
        self.start_registration()
        response = self.callback()
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertEqual(SocialAccount.objects.get().user_id, self.victim.pk)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_existing_orcid_login_still_works_with_forged_identifiers(self):
        self.invited.invitation_completed_at = timezone.now()
        self.invited.save()
        SocialAccount.objects.create(
            user=self.invited, provider="orcid", uid="0000-0002-1234-5678"
        )
        session = self.client.session
        session["user_id"] = self.victim.pk
        session.save()
        self.begin({"user_id": "1"})
        self.callback(data={"user_id": "1"})
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)
        self.assertEqual(self.client.session.get_expiry_age(), 3600)
        self.assertEqual(SocialAccount.objects.count(), 1)

    def complete(self, client: Client, completion_url: str, **fields):
        return client.post(
            completion_url,
            {
                "email": self.invited.email,
                "first_name": "Invited",
                "last_name": "User",
                **fields,
            },
        )

    def test_registration_completion_authenticates_only_invited_user(self):
        self.validate_invitation()
        self.start_registration({"user_id": "1"})
        completion_url = self.callback().url
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(completion_url).status_code, 200)
        response = self.complete(self.client, completion_url, user_id="1")
        self.assertEqual(response.url, "/")
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)
        self.invited.refresh_from_db()
        self.assertEqual(self.invited.first_name, "Invited")
        self.assertTrue(self.invited.is_staff)
        self.assertIsNotNone(self.invited.invitation_completed_at)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertNotIn(COMPLETION_SESSION_KEY, self.client.session)
        self.assertEqual(self.client.post(completion_url).url, reverse("admin:login"))

    def test_completion_form_proposes_orcid_names(self):
        self.validate_invitation()
        self.start_registration()
        response = self.client.get(self.callback().url)
        self.assertEqual(response.context["form"].initial["first_name"], "ORCID")
        self.assertEqual(response.context["form"].initial["last_name"], "User")
        self.assertEqual(
            response.context["form"].initial["email"], "invited@example.com"
        )

    def test_completion_cannot_be_used_in_another_session(self):
        self.validate_invitation()
        self.start_registration()
        completion_url = self.callback().url
        other_client = Client()
        self.assertEqual(other_client.get(completion_url).url, reverse("admin:login"))
        response = self.complete(
            other_client, completion_url, email="stolen@example.com"
        )
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn("_auth_user_id", other_client.session)
        self.invited.refresh_from_db()
        self.assertEqual(self.invited.email, "invited@example.com")
        self.assertIsNone(self.invited.invitation_completed_at)

    def test_completion_requires_its_own_token(self):
        self.validate_invitation()
        self.start_registration()
        self.callback()
        forged_url = reverse("complete_registration_orcid", args=("forged-token",))
        self.assertEqual(self.client.get(forged_url).url, reverse("admin:login"))
        self.assertNotIn(COMPLETION_SESSION_KEY, self.client.session)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_expired_completion_cannot_modify_account(self):
        self.validate_invitation()
        self.start_registration()
        completion_url = self.callback().url
        session = self.client.session
        session[COMPLETION_SESSION_KEY] = {
            **session[COMPLETION_SESSION_KEY],
            "created_at": int(timezone.now().timestamp()) - COMPLETION_MAX_AGE,
        }
        session.save()
        response = self.complete(
            self.client, completion_url, email="expired@example.com"
        )
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertNotIn(COMPLETION_SESSION_KEY, self.client.session)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.invited.refresh_from_db()
        self.assertEqual(self.invited.email, "invited@example.com")
        self.assertIsNone(self.invited.invitation_completed_at)

    def test_incomplete_account_is_asked_to_complete_at_next_orcid_login(self):
        SocialAccount.objects.create(
            user=self.invited, provider="orcid", uid="0000-0002-1234-5678"
        )
        self.begin()
        response = self.callback()
        self.assertIn("/registration/orcid/verify/", response.url)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_connect_process_is_refused(self):
        for linked in (False, True):
            with self.subTest(linked=linked):
                SocialAccount.objects.all().delete()
                if linked:
                    SocialAccount.objects.create(
                        user=self.victim, provider="orcid", uid=DEFAULT_UID
                    )
                self.client.force_login(self.victim)
                self.begin({"process": "connect"})
                response = self.callback()
                self.assertEqual(response.url, reverse("admin:login"))
                self.assertEqual(SocialAccount.objects.count(), int(linked))

    def test_native_oauth_state_validation_rejects_wrong_state(self):
        self.validate_invitation()
        self.start_registration()
        response = self.client.get(
            self.callback_url, {"state": "wrong-state", "code": "valid-test-code"}
        )
        self.assertEqual(response.url, reverse("admin:login"))
        self.assert_no_association()

    def test_other_oauth_attempt_in_session_cannot_use_the_invitation(self):
        self.validate_invitation()
        self.start_registration()
        # Valid for Social Auth, but not the attempt started from the invitation.
        self.begin()
        response = self.callback()
        self.assertEqual(response.url, reverse("admin:login"))
        self.assert_no_association()
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)

    def test_deleted_target_during_oauth_is_rejected(self):
        self.validate_invitation()
        self.start_registration()
        User.objects.filter(pk=self.invited.pk).delete()
        response = self.callback()
        self.assertEqual(response.url, reverse("admin:login"))
        self.assertFalse(SocialAccount.objects.exists())
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
        self.assertFalse(SocialAccount.objects.exists())
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
