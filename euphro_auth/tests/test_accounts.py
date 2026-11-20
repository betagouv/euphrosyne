import datetime
import re
from unittest.mock import patch

import pytest
from allauth.account.models import EmailAddress
from django.contrib import auth
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client
from django.urls import reverse

from euphro_auth.models import User
from euphro_auth.tokens import PasswordResetTokenGenerator

pytestmark = pytest.mark.django_db
PASSWORD = "T8!vQ2#rM6@zL9$p"
NEW_PASSWORD = "Q4#wR7!tY2@uI9$o"


@pytest.fixture(autouse=True)
def local_static_storage(settings):
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


@pytest.fixture(name="user")
def password_user():
    return User.objects.create_user(
        email="user@example.com", password=PASSWORD, is_staff=True
    )


def login(client: Client, email: str, password: str):
    return client.post(reverse("account_login"), {"login": email, "password": password})


def request_reset(client: Client, email: str):
    return client.post(reverse("account_reset_password"), {"email": email})


def reset_link() -> str:
    body = str(mail.outbox[-1].body)
    match = re.search(r"https?://[^/\s]+(/accounts/password/reset/key/\S+/)", body)
    assert match
    return match.group(1)


def test_password_reset_sets_a_new_password(client, user):
    assert request_reset(client, user.email.upper()).status_code == 302
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    assert mail.outbox[0].subject.startswith("[Euphrosyne] ")

    response = client.get(reset_link(), follow=True)
    assert response.status_code == 200
    response = client.post(
        response.redirect_chain[-1][0],
        {"password1": NEW_PASSWORD, "password2": NEW_PASSWORD},
    )
    assert response.status_code == 302
    assert login(Client(), user.email, NEW_PASSWORD).status_code == 302


def test_password_reset_sends_nothing_for_unknown_or_passwordless_accounts(client):
    User.objects.create_user(email="orcid-only@example.com", password=None)
    request_reset(client, "orcid-only@example.com")
    request_reset(client, "unknown@example.com")
    assert not mail.outbox


def test_password_reset_link_expires_after_one_hour(user):
    generator = PasswordResetTokenGenerator()
    issued_at = datetime.datetime.now()
    with patch.object(generator, "_now", return_value=issued_at):
        token = generator.make_token(user)
    for age, valid in [(59, True), (61, False)]:
        later = issued_at + datetime.timedelta(minutes=age)
        with patch.object(generator, "_now", return_value=later):
            assert generator.check_token(user, token) is valid


def test_invitation_links_keep_three_days_of_validity(user):
    issued_at = datetime.datetime.now()
    with patch.object(default_token_generator, "_now", return_value=issued_at):
        token = default_token_generator.make_token(user)
    later = issued_at + datetime.timedelta(days=2)
    with patch.object(default_token_generator, "_now", return_value=later):
        assert default_token_generator.check_token(user, token)


def test_signup_is_closed(client):
    response = client.post(
        reverse("account_signup"),
        {"email": "new@example.com", "password1": PASSWORD, "password2": PASSWORD},
    )
    assert response.status_code == 200
    assert not User.objects.filter(email="new@example.com").exists()


@pytest.mark.parametrize("path", ["/accounts/email/", "/accounts/3rdparty/"])
def test_account_management_pages_are_not_offered(client, user, path):
    client.force_login(user)
    assert client.get(path).status_code == 404


def test_replaced_email_address_no_longer_signs_in(client, user):
    request_reset(client, user.email)
    assert EmailAddress.objects.filter(email="user@example.com").exists()
    user.email = "renamed@example.com"
    user.save()

    assert login(client, "user@example.com", PASSWORD).status_code == 200
    assert login(client, "renamed@example.com", PASSWORD).status_code == 302
    mail.outbox.clear()
    request_reset(Client(), "user@example.com")
    assert not mail.outbox


def test_sign_in_does_not_touch_email_addresses(user, django_assert_num_queries):
    EmailAddress.objects.create(user=user, email="old@example.com")
    with django_assert_num_queries(1):
        auth.models.update_last_login(None, user)
    assert EmailAddress.objects.filter(email="old@example.com").exists()


def test_logout_url_signs_out_and_returns_to_login(client, user):
    client.force_login(user)
    response = client.post(f"{reverse('admin:logout')}?next=/login/")
    assert response.status_code == 302
    assert response.url == "/login/"
    assert not auth.get_user(client).is_authenticated


def test_admin_password_change_uses_account_page(client, user):
    client.force_login(user)
    response = client.get(reverse("admin:password_change"))
    assert response.url == reverse("account_change_password")
    response = client.post(
        reverse("account_change_password"),
        {"oldpassword": PASSWORD, "password1": NEW_PASSWORD, "password2": NEW_PASSWORD},
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
