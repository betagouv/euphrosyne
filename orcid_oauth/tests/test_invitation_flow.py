from copy import deepcopy
from datetime import datetime, timedelta
from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.tokens import default_token_generator
from django.test import Client, TestCase, override_settings
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from euphro_auth.models import User

from ..invitations import CONTEXT_MAX_AGE, INVITATION_SESSION_KEY
from .helpers import (
    DEFAULT_UID,
    STATES_SESSION_KEY,
    latest_oauth_state,
    orcid_callback,
    start_orcid_login,
)

OAUTH_STATES_SESSION_KEY = STATES_SESSION_KEY
LOGIN_URL = reverse_lazy("account_login")
COMPLETION_URL = reverse_lazy("complete_registration_orcid")


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
        # The invitation page's ORCID button posts to the ORCID login view.
        return self.begin(data)

    def begin(self, data: dict | None = None, query: str = ""):
        return start_orcid_login(self.client, data, query)

    def callback(self, uid: str = DEFAULT_UID, *, data: dict | None = None):
        # Only remote ORCID responses are mocked. OAuth state validation, the
        # adapter, associations and Django authentication all run.
        return orcid_callback(self.client, uid, data=data)

    def assert_signup_closed(self, response) -> None:
        self.assertTemplateUsed(response, "account/signup_closed.html")
        self.assert_no_association()

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
        self.assert_signup_closed(response)

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
        response = self.callback()
        self.assert_signup_closed(response)
        self.assertContains(response, "connecté à un compte existant")
        self.assertContains(response, f'href="{LOGIN_URL}"')

    def test_orcid_is_offered_only_with_a_validated_invitation_link(self):
        response = self.client.get(self.register_url)
        self.assertFalse(response.context["orcid_registration_available"])
        self.validate_invitation()
        response = self.client.get(self.register_url)
        self.assertTrue(response.context["orcid_registration_available"])
        self.assertContains(response, f'action="{self.begin_url}"')

    def test_another_invitation_page_clears_the_invitation(self):
        self.validate_invitation()
        other_page = reverse(
            "registration_token",
            args=(urlsafe_base64_encode(force_bytes(self.victim.pk)), "registration"),
        )
        self.assertEqual(self.client.get(other_page).status_code, 200)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.begin()
        self.callback()
        self.assert_no_association()

    def test_orcid_start_requires_a_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.get(client.get(self.invitation_url(self.invited)).url)
        response = start_orcid_login(client)
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
        self.callback()
        self.assertEqual(SocialAccount.objects.get().user_id, self.invited.pk)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)

    def test_form_and_callback_identifiers_cannot_change_validated_target(self):
        self.validate_invitation()
        forged = {"user_id": "1", "uid": "1", "email": self.victim.email}
        self.begin(forged, query="?user_id=1")
        self.callback(data=forged)
        self.assertEqual(SocialAccount.objects.get().user_id, self.invited.pk)
        self.assertFalse(SocialAccount.objects.filter(user=self.victim).exists())
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)

    def test_expired_or_inconsistent_context_is_rejected(self):
        for changes in (
            {"validated_at": int(timezone.now().timestamp()) - CONTEXT_MAX_AGE},
            {"validated_at": int(timezone.now().timestamp()) + 60},
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
                self.start_registration()
                response = self.callback()
                self.assertEqual(response.url, LOGIN_URL)
                self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
                self.assert_no_association()

    def test_context_is_single_use_even_with_an_old_session_snapshot(self):
        self.validate_invitation()
        self.start_registration()
        old_context = deepcopy(self.client.session[INVITATION_SESSION_KEY])
        self.callback()
        self.client.logout()
        session = self.client.session
        session[INVITATION_SESSION_KEY] = old_context
        session.save()
        self.begin()
        response = self.callback(uid="0000-0009-9999-9999")
        self.assertEqual(response.url, LOGIN_URL)
        self.assertNotIn(INVITATION_SESSION_KEY, self.client.session)
        self.assertEqual(SocialAccount.objects.count(), 1)

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

    def test_orcid_associated_with_another_account_cannot_use_invitation(self):
        SocialAccount.objects.create(
            user=self.victim, provider="orcid", uid="0000-0002-1234-5678"
        )
        self.validate_invitation()
        self.start_registration()
        response = self.callback()
        self.assertEqual(response.url, LOGIN_URL)
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

    def test_orcid_registration_asks_to_complete_the_account(self):
        self.validate_invitation()
        self.start_registration({"user_id": "1"})
        self.callback()
        self.assertEqual(self.client.get("/").url, COMPLETION_URL)
        self.assertEqual(self.client.get(COMPLETION_URL).status_code, 200)
        response = self.complete(self.client, COMPLETION_URL, user_id="1")
        self.assertEqual(response.url, "/")
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)
        self.invited.refresh_from_db()
        self.assertEqual(self.invited.first_name, "Invited")
        self.assertTrue(self.invited.is_staff)
        self.assertIsNotNone(self.invited.invitation_completed_at)
        self.assertEqual(self.client.get(COMPLETION_URL).url, "/")

    def test_completion_form_proposes_orcid_names(self):
        self.validate_invitation()
        self.start_registration()
        self.callback()
        response = self.client.get(COMPLETION_URL)
        self.assertEqual(response.context["form"].initial["first_name"], "ORCID")
        self.assertEqual(response.context["form"].initial["last_name"], "User")
        self.assertEqual(response.context["form"].instance.email, "invited@example.com")

    def test_completion_requires_sign_in(self):
        response = self.complete(self.client, COMPLETION_URL, email="x@example.com")
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))
        self.invited.refresh_from_db()
        self.assertEqual(self.invited.email, "invited@example.com")

    def test_incomplete_account_is_asked_to_complete_at_next_orcid_login(self):
        SocialAccount.objects.create(
            user=self.invited, provider="orcid", uid="0000-0002-1234-5678"
        )
        self.begin()
        self.callback()
        self.assertEqual(auth.get_user(self.client).pk, self.invited.pk)
        self.assertEqual(self.client.get("/").url, COMPLETION_URL)

    def test_connect_process_is_refused(self):
        self.victim.invitation_completed_at = timezone.now()
        self.victim.save()
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
                self.assertEqual(response.url, LOGIN_URL)
                self.assertEqual(SocialAccount.objects.count(), int(linked))

    def test_native_oauth_state_validation_rejects_wrong_state(self):
        self.validate_invitation()
        self.start_registration()
        response = self.client.get(
            self.callback_url, {"state": "wrong-state", "code": "valid-test-code"}
        )
        self.assertTemplateUsed(response, "socialaccount/authentication_error.html")
        self.assertContains(response, f'href="{LOGIN_URL}"', status_code=401)
        self.assert_no_association()

    def test_cancelled_orcid_sign_in_offers_to_sign_in_again(self):
        self.begin()
        response = self.client.get(
            self.callback_url,
            {"state": self.oauth_state(), "error": "access_denied"},
            follow=True,
        )
        self.assertTemplateUsed(response, "socialaccount/login_cancelled.html")
        self.assertContains(response, f'href="{LOGIN_URL}"')
        self.assert_no_association()

    def test_deleted_target_during_oauth_is_rejected(self):
        self.validate_invitation()
        self.start_registration()
        User.objects.filter(pk=self.invited.pk).delete()
        response = self.callback()
        self.assertEqual(response.url, LOGIN_URL)
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
