from unittest.mock import patch

import pytest
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    PasswordChangeForm,
    SetPasswordForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet

from euphro_auth.forms import UserCreationForm, UserInvitationRegistrationForm
from euphro_auth.models import User


@pytest.mark.parametrize("role", [{}, {"is_staff": True}])
def test_ordinary_users_require_twelve_characters(role):
    user = User(email="person@example.org", **role)
    validate_password("Q7!vR2#xM9@z", user)
    with pytest.raises(ValidationError, match="12"):
        validate_password("Q7!vR2#xM9@", user)


@pytest.mark.parametrize("role", [{"is_superuser": True}, {"is_lab_admin": True}])
def test_administrators_require_sixteen_characters(role):
    user = User(email="person@example.org", **role)
    validate_password("Q7!vR2#xM9@zL8$p", user)
    with pytest.raises(ValidationError, match="16"):
        validate_password("Q7!vR2#xM9@zL8$", user)


@pytest.mark.parametrize(
    "password",
    [
        "qzvtrpks",
        "qzvtrpksmnbvcxza",
        "q7!vr2#xm9@zl8$p",
        "Q7!VR2#XM9@ZL8$P",
        "Qv!rMx#zLp@bNs$k",
        "Q7vrR2xmM9zL8pKs",
    ],
)
def test_passwords_missing_character_types_are_rejected(password):
    with pytest.raises(ValidationError) as error:
        validate_password(password, User(email="person@example.org"))
    assert "password_missing_character_types" in [
        item.code for item in error.value.error_list
    ]


@pytest.mark.parametrize(
    "form_class",
    [
        SetPasswordForm,
        PasswordChangeForm,
        AdminPasswordChangeForm,
        UserInvitationRegistrationForm,
    ],
)
@pytest.mark.parametrize("role", [{}, {"is_lab_admin": True}, {"is_superuser": True}])
def test_password_forms_enforce_policy(form_class, role):
    user = User(email="person@example.org", **role)
    user.set_password("PreviousQ7!vR2#xM")
    for password, valid in [
        ("qzvtrpks", False),
        ("Q7!vR2#xM9@z", not role),
        ("Q7!vR2#xM9@zL8$p", True),
    ]:
        form = form_class(
            user=user,
            data={
                "email": user.email,
                "first_name": "Alice",
                "last_name": "Martin",
                "old_password": "PreviousQ7!vR2#xM",
                "new_password1": password,
                "new_password2": password,
                "password1": password,
                "password2": password,
            },
        )
        assert form.is_valid() == valid, form.errors


@pytest.mark.django_db
@pytest.mark.parametrize(
    "password,valid", [("qzvtrpks", False), ("Q7!vR2#xM9@z", True)]
)
def test_creation_form_enforces_policy(password, valid):
    form = UserCreationForm(
        data={
            "email": "person@example.org",
            "password1": password,
            "password2": password,
        }
    )
    assert form.is_valid() == valid, form.errors


@pytest.mark.parametrize("field", ["email", "first_name", "last_name"])
def test_invitation_checks_submitted_identity(field):
    password = "ZelvoriaQ7!xy"
    data = {
        "email": "person@example.org",
        "first_name": "Alice",
        "last_name": "Martin",
        "new_password1": password,
        "new_password2": password,
    }
    data[field] = password if field != "email" else password + "@example.org"
    user = User(email="person@example.org")
    form = UserInvitationRegistrationForm(user=user, data=data)
    with patch.object(QuerySet, "exists", return_value=False):
        assert not form.is_valid()
    assert form.has_error("new_password2", "password_too_similar")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method,role",
    [
        ("create_user", {}),
        ("create_user", {"is_lab_admin": True}),
        ("create_superuser", {}),
    ],
)
def test_manager_rejects_passwords_before_saving(method, role):
    create = getattr(User.objects, method)
    for password in ["foo", "qzvtrpksmnbvcxza"]:
        with pytest.raises(ValidationError):
            create(email="person@example.org", password=password, **role)
    with pytest.raises(ValidationError):
        create(
            email="person@example.org",
            password="ZelvoriaQ7!xyZ2@p",
            first_name="ZelvoriaQ7!xyZ2@p",
            **role,
        )
    assert not User.objects.exists()
    if method == "create_superuser" or role:
        with pytest.raises(ValidationError):
            create(email="person@example.org", password="Q7!vR2#xM9@z", **role)
    user = create(email="person@example.org", password="Q7!vR2#xM9@zL8$p", **role)
    user.refresh_from_db()
    assert user.check_password("Q7!vR2#xM9@zL8$p")


@pytest.mark.django_db
def test_manager_allows_accounts_without_local_password():
    user = User.objects.create_user(email="person@example.org", password=None)
    assert not user.has_usable_password()
