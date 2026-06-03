import json

from django.test import TestCase

from euphro_auth.tests import factories as auth_factories
from lab.tests import factories as lab_factories


class NotebookViewTestCase(TestCase):
    def test_notebook_json_data_contains_data_file_metadata(self):
        project = lab_factories.ProjectFactory(is_data_available=True)
        run = lab_factories.RunFactory(
            project=project,
            label="20260224_Protons3MeV",
        )
        user = auth_factories.LabAdminUserFactory()

        self.client.force_login(user)
        response = self.client.get(f"/lab/run/{run.id}/notebook")

        assert response.status_code == 200
        json_data = json.loads(response.context["json_data"])
        assert json_data == {
            "runId": str(run.id),
            "projectId": str(project.id),
            "projectSlug": project.slug,
            "runLabel": run.label,
            "isDataAvailable": True,
        }
