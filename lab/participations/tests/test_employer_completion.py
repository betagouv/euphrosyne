from unittest import mock

from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.tests import factories as auth_factories
from lab.tests import factories


class TestEmployerCompletionWorkflow(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = auth_factories.StaffUserFactory()
        self.project = factories.ProjectFactory()
        self.participation = factories.ParticipationFactory(
            user=self.user,
            project=self.project,
            on_premises=True,
            employer=None,
            institution=factories.InstitutionFactory(ror_id="https://ror.org/non"),
        )
        self.client.force_login(self.user)

    def test_incomplete_participation_redirects_project_page_to_completion(self):
        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.project.id])
        )

        assert response.status_code == 302
        assert response["Location"] == reverse(
            "participation_employer_completion",
            kwargs={"project_id": self.project.id},
        )

    def test_incomplete_participation_redirects_run_page_to_completion(self):
        run = factories.RunFactory(project=self.project)

        response = self.client.get(reverse("admin:lab_run_change", args=[run.id]))

        assert response.status_code == 302
        assert response["Location"] == reverse(
            "participation_employer_completion",
            kwargs={"project_id": self.project.id},
        )

    def test_malformed_run_change_object_id_does_not_crash(self):
        response = self.client.get(f"/lab/run/{self.project.id}/notebook/change/")

        assert response.status_code == 302
        assert response["Location"] != reverse(
            "participation_employer_completion",
            kwargs={"project_id": self.project.id},
        )

    def test_completion_page_is_rendered(self):
        response = self.client.get(
            reverse(
                "participation_employer_completion",
                kwargs={"project_id": self.project.id},
            )
        )

        assert response.status_code == 200
        self.assertTemplateUsed(response, "lab/participations/employer_completion.html")
        assert list(response.context["form"].fields) == [
            "email",
            "first_name",
            "last_name",
            "function",
        ]

    def test_completion_form_is_prefilled_from_previous_same_institution(self):
        previous_employer = factories.EmployerFactory(
            email="previous.manager@example.com",
            first_name="Jane",
            last_name="Manager",
            function="Director",
        )
        factories.ParticipationFactory(
            user=self.user,
            institution=self.participation.institution,
            employer=previous_employer,
        )

        response = self.client.get(
            reverse(
                "participation_employer_completion",
                kwargs={"project_id": self.project.id},
            )
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert 'value="previous.manager@example.com"' in content
        assert 'value="Jane"' in content
        assert 'value="Manager"' in content
        assert 'value="Director"' in content

    def test_incomplete_participation_blocks_project_api_with_completion_url(self):
        response = self.client.get(
            reverse(
                "api:project-on-premises-participation-list-create",
                kwargs={"project_id": self.project.id},
            )
        )

        assert response.status_code == 403
        assert response.json()["completion_url"] == reverse(
            "participation_employer_completion",
            kwargs={"project_id": self.project.id},
        )

    def test_completion_form_saves_employer_and_restores_access(self):
        response = self.client.post(
            reverse(
                "participation_employer_completion",
                kwargs={"project_id": self.project.id},
            ),
            data={
                "email": "manager@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "function": "Manager",
            },
        )

        assert response.status_code == 302
        self.participation.refresh_from_db()
        assert self.participation.employer is not None
        assert self.participation.employer.email == "manager@example.com"

        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.project.id])
        )
        assert response.status_code == 200

    def test_lab_admin_is_not_redirected(self):
        admin = auth_factories.LabAdminUserFactory()
        self.client.force_login(admin)

        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.project.id])
        )

        assert response.status_code == 200

    def test_complete_project_leader_is_not_blocked_by_other_participant(self):
        self.participation.is_leader = True
        self.participation.employer = factories.EmployerFactory()
        self.participation.save()
        factories.ParticipationFactory(
            project=self.project,
            on_premises=True,
            employer=None,
            institution=factories.InstitutionFactory(ror_id="https://ror.org/non"),
        )

        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.project.id])
        )

        assert response.status_code == 200

    def test_remote_participant_with_missing_employer_is_not_redirected(self):
        self.participation.on_premises = False
        self.participation.save()

        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.project.id])
        )

        assert response.status_code == 200

    @mock.patch("lab.participations.employer_workflow.apps.is_installed")
    def test_feature_disabled_does_not_block_project_access(self, mock_is_installed):
        mock_is_installed.return_value = False

        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.project.id])
        )

        assert response.status_code == 200
