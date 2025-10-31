from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from lab.models import Project

from ...tests import factories
from ..models import Employer, Institution, Participation


class TestParticipationModel(TestCase):
    def test_user_can_participate_only_once_in_project(self):
        user = get_user_model().objects.create(
            email="user@test.test", password="password"
        )
        project = Project.objects.create(name="Project Test")
        Participation.objects.create(user=user, project=project)
        with self.assertRaises(IntegrityError):
            Participation.objects.create(user=user, project=project)

    def test_project_can_only_have_one_leader_participation(self):
        leader = get_user_model().objects.create(
            email="leader@test.test", password="password"
        )
        leader_wanabe = get_user_model().objects.create(
            email="leader2@test.test", password="password"
        )
        project = Project.objects.create(name="Project Test")
        Participation.objects.create(user=leader, project=project, is_leader=True)
        with self.assertRaises(IntegrityError):
            Participation.objects.create(
                user=leader_wanabe, project=project, is_leader=True
            )

    def test_participation_with_employer(self):
        user = get_user_model().objects.create(
            email="user@test.test", password="password"
        )
        project = factories.ProjectFactory(name="Project Test")
        employer = factories.EmployerFactory()
        participation = factories.ParticipationFactory(
            user=user, project=project, employer=employer, on_premises=True
        )
        assert participation.employer == employer
        assert participation.on_premises is True

    def test_participation_without_employer(self):
        user = get_user_model().objects.create(
            email="user@test.test", password="password"
        )
        project = factories.ProjectFactory(name="Project Test")
        participation = factories.ParticipationFactory(
            user=user, project=project, on_premises=False
        )
        assert participation.employer is None
        assert participation.on_premises is False

    def test_participation_str_method(self):
        user = get_user_model().objects.create(
            email="user@test.test", password="password"
        )
        project = Project.objects.create(name="Project Test")
        participation = Participation.objects.create(user=user, project=project)
        assert str(participation) == f"{user} participation in {project}"


class TestEmployerModel(TestCase):
    def test_create_employer(self):
        employer = Employer.objects.create(
            email="employer@test.test",
            first_name="John",
            last_name="Doe",
            function="Manager",
        )
        assert employer.email == "employer@test.test"
        assert employer.first_name == "John"
        assert employer.last_name == "Doe"
        assert employer.function == "Manager"

    def test_employer_str_method(self):
        employer = Employer.objects.create(
            email="employer@test.test",
            first_name="John",
            last_name="Doe",
            function="Manager",
        )
        assert str(employer) == "John Doe"


class TestInstitutionModel(TestCase):
    def test_create_institution_with_country(self):
        institution = Institution.objects.create(
            name="Test Institution", country="France"
        )
        assert institution.name == "Test Institution"
        assert institution.country == "France"

    def test_create_institution_without_country(self):
        institution = Institution.objects.create(name="Test Institution")
        assert institution.name == "Test Institution"
        assert institution.country is None

    def test_institution_str_with_country(self):
        institution = Institution.objects.create(
            name="Test Institution", country="France"
        )
        assert str(institution) == "Test Institution, France"

    def test_institution_str_without_country(self):
        institution = Institution.objects.create(name="Test Institution")
        assert str(institution) == "Test Institution"

    def test_institution_unique_constraint(self):
        Institution.objects.create(
            name="Test Institution", country="France", ror_id="123"
        )
        with self.assertRaises(IntegrityError):
            Institution.objects.create(
                name="Test Institution", country="France", ror_id="123"
            )
