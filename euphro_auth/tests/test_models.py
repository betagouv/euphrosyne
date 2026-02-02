import pytest
from django.contrib.auth import get_user_model

from euphro_auth.tests import factories


@pytest.mark.django_db
def test_user_get_administrative_name():
    """Test the get_administrative_name method."""
    user = factories.StaffUserFactory(first_name="John", last_name="Doe")
    assert user.get_administrative_name() == "DOE John"


@pytest.mark.django_db
def test_user_get_administrative_name_empty_names():
    """Test get_administrative_name with empty names."""
    user = factories.StaffUserFactory(first_name="", last_name="")
    assert user.get_administrative_name() == ""


@pytest.mark.django_db
def test_user_get_administrative_name_only_last_name():
    """Test get_administrative_name with only last name."""
    user = factories.StaffUserFactory(first_name="", last_name="Doe")
    assert user.get_administrative_name() == "DOE"


@pytest.mark.django_db
def test_user_get_administrative_name_only_first_name():
    """Test get_administrative_name with only first name."""
    user = factories.StaffUserFactory(first_name="John", last_name="")
    assert user.get_administrative_name() == "John"


@pytest.mark.django_db
def test_user_get_administrative_name_with_spaces():
    """Test get_administrative_name with names containing spaces."""
    user = factories.StaffUserFactory(
        first_name="Jean Pierre", last_name="De La Fontaine"
    )
    assert user.get_administrative_name() == "DE LA FONTAINE Jean Pierre"


@pytest.mark.django_db
def test_user_name_normalization_lowercase():
    user = get_user_model().objects.create(
        email="user@test.test",
        password="password",
        first_name="jean-pierre",
        last_name="o'neill",
    )
    assert user.first_name == "Jean-Pierre"
    assert user.last_name == "O'Neill"


@pytest.mark.django_db
def test_user_name_normalization_uppercase():
    user = get_user_model().objects.create(
        email="user2@test.test",
        password="password",
        first_name="JEAN PIERRE",
        last_name="O'NEILL",
    )
    assert user.first_name == "Jean Pierre"
    assert user.last_name == "O'Neill"


@pytest.mark.django_db
def test_user_name_normalization_mixed_case_unchanged():
    user = get_user_model().objects.create(
        email="user3@test.test",
        password="password",
        first_name="McDonald",
        last_name="van Helsing",
    )
    assert user.first_name == "McDonald"
    assert user.last_name == "van Helsing"
