from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from lab.api_views.serializers import (
    OnPremisesParticipationSerializer,
    ParticipationSerializer,
    ProjectUserUniqueValidator,
)
from lab.participations.models import Employer, Institution

from .. import factories


class TestParticipationSerializer(TestCase):
    @mock.patch("lab.api_views.serializers.send_project_invitation_email")
    @mock.patch("lab.api_views.serializers.send_invitation_email")
    def test_serializer_create_with_new_user_and_institution(
        self, mock_send_invitation, mock_send_project_invitation
    ):
        project = factories.ProjectFactory()
        data = {
            "user": {"email": "newuser@test.test"},
            "institution": {
                "name": "New Institution",
                "country": "France",
                "ror_id": "123",
            },
        }
        serializer = ParticipationSerializer(data=data, context={"project": project})
        assert serializer.is_valid()

        participation = serializer.save(project=project)
        assert participation.user.email == "newuser@test.test"
        assert participation.institution.name == "New Institution"
        assert participation.institution.country == "France"
        assert participation.institution.ror_id == "123"

        # Check that invitation emails were sent
        mock_send_invitation.assert_called_once_with(participation.user)
        mock_send_project_invitation.assert_called_once_with(
            participation.user.email, project
        )

    @mock.patch("lab.api_views.serializers.send_project_invitation_email")
    @mock.patch("lab.api_views.serializers.send_invitation_email")
    def test_serializer_create_with_existing_user(
        self, mock_send_invitation, mock_send_project_invitation
    ):
        existing_user = get_user_model().objects.create(email="existing@test.test")
        project = factories.ProjectFactory()
        data = {
            "user": {"email": "existing@test.test"},
            "institution": {
                "name": "New Institution",
                "country": "France",
            },
        }
        serializer = ParticipationSerializer(data=data, context={"project": project})
        assert serializer.is_valid()

        participation = serializer.save(project=project)
        assert participation.user == existing_user

        # Existing user should not get invitation email, only project invitation
        mock_send_invitation.assert_not_called()
        mock_send_project_invitation.assert_called_once_with(
            existing_user.email, project
        )

    def test_serializer_create_with_existing_institution(self):
        existing_institution = Institution.objects.create(
            name="Existing Institution", country="France", ror_id="123"
        )
        project = factories.ProjectFactory()
        data = {
            "user": {"email": "newuser@test.test"},
            "institution": {
                "name": "Existing Institution",
                "country": "France",
                "ror_id": "123",
            },
        }
        serializer = ParticipationSerializer(data=data, context={"project": project})
        assert serializer.is_valid()

        participation = serializer.save(project=project)
        assert participation.institution == existing_institution

    def test_serializer_update_institution(self):
        participation = factories.ParticipationFactory()
        factories.InstitutionFactory(name="Updated Institution", country="Germany")
        data = {
            "institution": {
                "name": "Updated Institution",
                "country": "Germany",
            }
        }
        serializer = ParticipationSerializer(
            instance=participation, data=data, partial=True
        )
        assert serializer.is_valid()

        updated_participation = serializer.save()
        assert updated_participation.institution.name == "Updated Institution"
        assert updated_participation.institution.country == "Germany"

    def test_serializer_fields(self):
        serializer = ParticipationSerializer()
        assert "id" in serializer.fields
        assert "user" in serializer.fields
        assert "institution" in serializer.fields
        assert "on_premises" in serializer.fields


class TestOnPremisesParticipationSerializer(TestCase):
    @mock.patch("lab.api_views.serializers.send_project_invitation_email")
    @mock.patch("lab.api_views.serializers.send_invitation_email")
    def test_serializer_create_with_employer(
        self, mock_send_invitation, mock_send_project_invitation
    ):
        project = factories.ProjectFactory()
        data = {
            "user": {"email": "newuser@test.test"},
            "institution": {
                "name": "New Institution",
                "country": "France",
            },
            "employer": {
                "email": "employer@test.test",
                "first_name": "John",
                "last_name": "Doe",
                "function": "Manager",
            },
        }
        serializer = OnPremisesParticipationSerializer(
            data=data, context={"project": project}
        )
        assert serializer.is_valid()

        participation = serializer.save(project=project)
        assert participation.user.email == "newuser@test.test"
        assert participation.employer is not None
        assert participation.employer.email == "employer@test.test"
        assert participation.employer.first_name == "John"
        assert participation.employer.last_name == "Doe"
        assert participation.employer.function == "Manager"

        # Check that invitation emails were sent
        mock_send_invitation.assert_called_once_with(participation.user)
        mock_send_project_invitation.assert_called_once_with(
            participation.user.email, project
        )

    def test_serializer_update_employer(self):
        employer = factories.EmployerFactory()
        participation = factories.ParticipationFactory(
            employer=employer, on_premises=True
        )

        data = {
            "employer": {
                "email": "new@test.test",
                "first_name": "New",
                "last_name": "Name",
                "function": "New Function",
            }
        }
        serializer = OnPremisesParticipationSerializer(
            instance=participation, data=data, partial=True
        )
        assert serializer.is_valid()

        serializer.save()
        # Refresh employer from database
        employer.refresh_from_db()
        assert employer.email == "new@test.test"
        assert employer.first_name == "New"
        assert employer.last_name == "Name"
        assert employer.function == "New Function"

    def test_serializer_create_employer_when_none(self):
        participation = factories.ParticipationFactory(on_premises=True, employer=None)
        initial_employer_count = Employer.objects.count()

        data = {
            "employer": {
                "email": "new@test.test",
                "first_name": "New",
                "last_name": "Name",
                "function": "New Function",
            }
        }
        serializer = OnPremisesParticipationSerializer(
            instance=participation, data=data, partial=True
        )
        assert serializer.is_valid()

        serializer.save()
        # The serializer creates a new employer
        # but doesn't assign it to the participation
        # This verifies that an employer is created
        assert Employer.objects.count() == initial_employer_count + 1
        new_employer = Employer.objects.latest("id")
        assert new_employer.email == "new@test.test"

    @mock.patch("lab.api_views.serializers.send_project_invitation_email")
    def test_serializer_update_with_new_user_email(self, mock_send_project_invitation):
        """Test updating participation with a new user email sends invitation."""
        participation = factories.ParticipationFactory(on_premises=True)

        data = {
            "user": {"email": "newemail@test.test"},
        }
        serializer = OnPremisesParticipationSerializer(
            instance=participation,
            data=data,
            partial=True,
            context={"project": participation.project},
        )
        assert serializer.is_valid()

        updated_participation = serializer.save()
        assert updated_participation.user.email == "newemail@test.test"

        # Should send project invitation to the new user
        mock_send_project_invitation.assert_called_once_with(
            "newemail@test.test", participation.project
        )

    @mock.patch("lab.api_views.serializers.send_project_invitation_email")
    def test_serializer_update_with_same_user_email_no_invitation(
        self, mock_send_project_invitation
    ):
        """Test updating participation with same user email does not send invitation."""
        participation = factories.ParticipationFactory(on_premises=True)
        old_user_email = participation.user.email

        data = {
            "user": {"email": old_user_email},
        }
        serializer = OnPremisesParticipationSerializer(
            instance=participation,
            data=data,
            partial=True,
            context={"project": participation.project},
        )
        assert serializer.is_valid()

        updated_participation = serializer.save()
        assert updated_participation.user.email == old_user_email

        # Should not send project invitation when user hasn't changed
        mock_send_project_invitation.assert_not_called()

    def test_serializer_has_employer_field(self):
        serializer = OnPremisesParticipationSerializer()
        assert "employer" in serializer.fields


class TestProjectUserUniqueValidator(TestCase):
    def test_validator_raises_error_if_user_already_participates(self):
        participation = factories.ParticipationFactory()
        validator = ProjectUserUniqueValidator()

        mock_field = mock.MagicMock()
        mock_field.context = {"project": participation.project}

        with self.assertRaises(Exception):
            validator({"email": participation.user.email}, mock_field)

    def test_validator_passes_if_user_does_not_participate(self):
        project = factories.ProjectFactory()
        validator = ProjectUserUniqueValidator()

        mock_field = mock.MagicMock()
        mock_field.context = {"project": project}

        # Should not raise an exception
        validator({"email": "newuser@test.test"}, mock_field)

    def test_validator_raises_error_without_project_in_context(self):
        validator = ProjectUserUniqueValidator()

        mock_field = mock.MagicMock()
        mock_field.context = {}

        with self.assertRaises(ValueError):
            validator({"email": "test@test.test"}, mock_field)

    def test_validator_raises_error_without_email_in_data(self):
        project = factories.ProjectFactory()
        validator = ProjectUserUniqueValidator()

        mock_field = mock.MagicMock()
        mock_field.context = {"project": project}

        with self.assertRaises(ValueError):
            validator({}, mock_field)

    def test_validator_allows_updating_same_user_email(self):
        """Test that validator allows updating a participation
        with the same user email."""
        participation = factories.ParticipationFactory()
        validator = ProjectUserUniqueValidator()

        mock_field = mock.MagicMock()
        mock_field.context = {"project": participation.project}
        mock_field.root.instance = participation

        # Should not raise an exception when updating with the same email
        validator({"email": participation.user.email}, mock_field)
