import pytest

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
