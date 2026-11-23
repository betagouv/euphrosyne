import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError
from django.forms import modelform_factory
from django.utils.translation import gettext

from euphro_auth.forms import UserChangeForm, UserCreationForm
from euphro_auth.models import User, UserInvitation

pytestmark = pytest.mark.django_db

PASSWORD = "T8!vQ2#rM6@zL9$p"


def email_error() -> str:
    return gettext("An account with this email already exists.")


def test_manager_stores_lowercase_email():
    user = User.objects.create_user(email=" Jane.Doe@Example.FR ", password=None)
    assert user.email == "jane.doe@example.fr"
    superuser = User.objects.create_superuser(
        email="Admin@Example.fr", password=PASSWORD
    )
    assert superuser.email == "admin@example.fr"


def test_natural_key_lookup_ignores_case():
    user = User.objects.create_user(email="jane.doe@example.fr", password=None)
    assert User.objects.get_by_natural_key("Jane.Doe@Example.FR") == user


def test_createsuperuser_reports_an_existing_email_whatever_its_case(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", PASSWORD)
    call_command("createsuperuser", email="admin@example.fr", interactive=False)
    with pytest.raises(CommandError, match="already taken"):
        call_command("createsuperuser", email="Admin@Example.fr", interactive=False)


def test_save_stores_lowercase_email():
    user = User.objects.create(email="Jane.Doe@Example.fr")
    assert user.email == "jane.doe@example.fr"

    user.email = "John.Doe@Example.fr"
    user.save(update_fields=["email"])
    user.refresh_from_db()
    assert user.email == "john.doe@example.fr"


def test_clean_lowercases_email():
    user = User(email="Jane.Doe@Example.fr")
    user.clean()
    assert user.email == "jane.doe@example.fr"
    invitation = UserInvitation(email="Jane.Doe@Example.fr")
    invitation.clean()
    assert invitation.email == "jane.doe@example.fr"
    assert invitation.is_staff


def test_database_rejects_emails_differing_by_case():
    User.objects.create(email="jane.doe@example.fr")
    with pytest.raises(IntegrityError):
        # bulk_create skips the lowercasing of User.save.
        User.objects.bulk_create([User(email="Jane.Doe@example.fr")])


@pytest.mark.parametrize("email", ["Jane.Doe@x.fr", "jane.doe@x.fr"])
def test_admin_creation_form_rejects_existing_email(email):
    User.objects.create(email="jane.doe@x.fr")
    form = UserCreationForm(
        data={"email": email, "password1": PASSWORD, "password2": PASSWORD}
    )
    assert not form.is_valid()
    assert form.errors == {"email": [email_error()]}


def test_admin_creation_form_saves_lowercase_email():
    form = UserCreationForm(
        data={"email": "Jane.Doe@x.fr", "password1": PASSWORD, "password2": PASSWORD}
    )
    assert form.is_valid(), form.errors
    assert form.save().email == "jane.doe@x.fr"


def test_admin_change_form_rejects_existing_email():
    User.objects.create(email="jane.doe@x.fr")
    user = User.objects.create(email="other@x.fr")
    form = UserChangeForm(instance=user, data={"email": "Jane.Doe@x.fr"})
    assert not form.is_valid()
    assert form.errors == {"email": [email_error()]}


def test_admin_change_form_accepts_own_email_in_another_case():
    user = User.objects.create(email="jane.doe@x.fr")
    form = UserChangeForm(instance=user, data={"email": "Jane.Doe@x.fr"})
    assert form.is_valid(), form.errors
    assert form.save().email == "jane.doe@x.fr"


def test_invitation_admin_form_rejects_existing_email():
    User.objects.create(email="jane.doe@x.fr")
    form_class = modelform_factory(
        UserInvitation, fields=("email", "first_name", "last_name")
    )
    form = form_class(
        data={"email": "Jane.Doe@x.fr", "first_name": "Jane", "last_name": "Doe"}
    )
    assert not form.is_valid()
    assert form.errors == {"email": [email_error()]}


def test_orcid_completion_form_rejects_existing_email():
    # pylint: disable=import-outside-toplevel
    from orcid_oauth.views import UserCompleteAccountView

    User.objects.create(email="jane.doe@x.fr")
    user = User.objects.create(email="orcid@x.fr")
    form_class = modelform_factory(User, fields=UserCompleteAccountView.fields)
    form = form_class(
        instance=user,
        data={"email": "Jane.Doe@x.fr", "first_name": "Jane", "last_name": "Doe"},
    )
    assert not form.is_valid()
    assert form.errors == {"email": [email_error()]}
