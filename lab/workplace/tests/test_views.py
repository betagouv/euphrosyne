import json

import pytest
from django.test import RequestFactory

from data_management.models import LifecycleState, ProjectData
from euphro_auth.tests.factories import LabAdminUserFactory
from lab.tests.factories import ProjectFactory, RunFactory
from lab.workplace.views import WorkplaceView


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("state", "expected_can_delete", "expected_can_delete_when_hot"),
    [
        (LifecycleState.HOT, True, True),
        (LifecycleState.COOL, False, True),
        (LifecycleState.COOLING, False, True),
        (LifecycleState.RESTORING, False, True),
        (LifecycleState.ERROR, False, True),
    ],
)
def test_workplace_view_delete_flags_follow_project_lifecycle(
    state: LifecycleState,
    expected_can_delete: bool,
    expected_can_delete_when_hot: bool,
):
    project = ProjectFactory()
    RunFactory(project=project)
    project_data = ProjectData.for_project(project)
    project_data.lifecycle_state = state
    project_data.save(update_fields=["lifecycle_state"])

    request = RequestFactory().get("/lab/project/%s/workplace" % project.id)
    request.user = LabAdminUserFactory()
    view = WorkplaceView()
    view.request = request
    view.project = project

    context = view.get_context_data()
    data = json.loads(context["json_data"])

    assert len(data["runs"]) == 1
    assert data["runs"][0]["rawDataTable"]["canDelete"] is expected_can_delete
    assert data["runs"][0]["processedDataTable"]["canDelete"] is expected_can_delete
    assert (
        data["runs"][0]["rawDataTable"]["canDeleteWhenHot"]
        is expected_can_delete_when_hot
    )
    assert (
        data["runs"][0]["processedDataTable"]["canDeleteWhenHot"]
        is expected_can_delete_when_hot
    )
    assert data["isLabAdmin"] is True
    assert data["project"]["lifecycleState"] == state
    assert data["project"]["lastLifecycleOperationId"] is None
    assert data["project"]["lastLifecycleOperationType"] is None
