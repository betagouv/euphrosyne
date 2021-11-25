from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet

from ...forms import UserInvitationRegistrationForm


def test_form_save_success():
    user = get_user_model()(email="test@test.test")
    form = UserInvitationRegistrationForm(
        data={
            "email": "test@test.test",
            "new_password1": "abcdef102",
            "new_password2": "abcdef102",
            "first_name": "John",
            "last_name": "Doe",
        },
        user=user,
    )

    assert form.is_valid()
    form.save(commit=False)
    assert user.email == "test@test.test"
    assert user.first_name == "John"
    assert user.last_name == "Doe"


def test_email_can_be_changed():
    user = get_user_model()(email="test@test.test")
    form = UserInvitationRegistrationForm(
        data={
            "email": "new_email@test.test",
            "new_password1": "abcdef102",
            "new_password2": "abcdef102",
            "first_name": "John",
            "last_name": "Doe",
        },
        user=user,
    )

    with patch.object(QuerySet, "exists", return_value=False):
        assert form.is_valid()
    form.save(commit=False)
    assert user.email == "new_email@test.test"


def test_email_should_be_unique():
    user = get_user_model()(email="test@test.test")
    form = UserInvitationRegistrationForm(
        data={
            "email": "anotheruser@test.test",
            "new_password1": "abcdef102",
            "new_password2": "abcdef102",
            "first_name": "John",
            "last_name": "Doe",
        },
        user=user,
    )
    with patch.object(QuerySet, "exists", return_value=True):
        assert not form.is_valid()
    assert form.has_error("email", code="invitation_email_already_exists")


def test_complete_invitation_on_save():
    user = get_user_model()(email="test@test.test")
    form = UserInvitationRegistrationForm(
        data={
            "email": "test@test.test",
            "new_password1": "abcdef102",
            "new_password2": "abcdef102",
            "first_name": "John",
            "last_name": "Doe",
        },
        user=user,
    )
    with patch.object(QuerySet, "exists", return_value=False):
        assert form.is_valid()
    form.save(commit=False)
    assert user.invitation_completed_at is not None
