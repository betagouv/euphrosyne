import json

import pytest
from django.test import RequestFactory

from data_management.models import LifecycleState, ProjectData
from euphro_auth.tests.factories import StaffUserFactory
from lab.documents.views import ProjectDocumentsView
from lab.tests.factories import ProjectFactory


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("state", "expected_can_write"),
    [
        (LifecycleState.HOT, True),
        (LifecycleState.COOL, False),
        (LifecycleState.COOLING, False),
    ],
)
def test_documents_view_write_flags_follow_project_lifecycle(
    state: LifecycleState,
    expected_can_write: bool,
):
    project = ProjectFactory()
    project_data = ProjectData.for_project(project)
    project_data.lifecycle_state = state
    project_data.save(update_fields=["lifecycle_state"])

    request = RequestFactory().get("/lab/project/%s/documents" % project.id)
    request.user = StaffUserFactory()
    view = ProjectDocumentsView()
    view.request = request
    view.project = project

    context = view.get_context_data()
    data = json.loads(context["json_data"])

    assert data["table"]["canDelete"] is expected_can_write
    assert data["form"]["canUpload"] is expected_can_write
