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
    def test_serializer_create_with_new_user_and_institution(self):
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

    def test_serializer_create_with_existing_user(self):
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
    def test_serializer_create_with_employer(self):
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
