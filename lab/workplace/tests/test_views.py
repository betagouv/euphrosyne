import json

import pytest
from django.test import RequestFactory
from django.utils.translation import gettext as _

from euphro_auth.tests.factories import LabAdminUserFactory
from lab.tests.factories import ProjectFactory, RunFactory
from lab.workplace.views import WorkplaceView


@pytest.mark.django_db
def test_workplace_view_exposes_data_management_feature_flag_for_lab_admin():
    project = ProjectFactory()
    RunFactory(project=project)

    request = RequestFactory().get("/lab/project/%s/workplace" % project.id)
    request.user = LabAdminUserFactory()
    view = WorkplaceView()
    view.request = request
    view.project = project

    context = view.get_context_data()
    data = json.loads(context["json_data"])

    assert len(data["runs"]) == 1
    assert data["runs"][0]["rawDataTable"]["canDelete"] is True
    assert data["runs"][0]["processedDataTable"]["canDelete"] is True
    assert "canDeleteWhenHot" not in data["runs"][0]["rawDataTable"]
    assert "canDeleteWhenHot" not in data["runs"][0]["processedDataTable"]
    assert data["isLabAdmin"] is True
    assert data["isDataManagementEnabled"] is True
    assert data["labels"]["dataManagementTitle"] == _("Data management")
    assert data["labels"]["loading"] == _("Loading")
    assert "lifecycleState" not in data["project"]
    assert "lastLifecycleOperationId" not in data["project"]
    assert "lastLifecycleOperationType" not in data["project"]
    assert context["can_start_vm"] is True


@pytest.mark.django_db
def test_workplace_view_uses_feature_flag_when_data_management_is_disabled(
    monkeypatch,
):
    project = ProjectFactory()
    RunFactory(project=project)

    monkeypatch.setattr(
        "lab.workplace.views.apps.is_installed",
        lambda app_label: app_label != "data_management",
    )

    request = RequestFactory().get("/lab/project/%s/workplace" % project.id)
    request.user = LabAdminUserFactory()
    view = WorkplaceView()
    view.request = request
    view.project = project

    context = view.get_context_data()
    data = json.loads(context["json_data"])

    assert data["runs"][0]["rawDataTable"]["canDelete"] is True
    assert data["runs"][0]["processedDataTable"]["canDelete"] is True
    assert data["isDataManagementEnabled"] is False
    assert data["labels"]["dataManagementTitle"] == _("Data management")
    assert data["labels"]["loading"] == _("Loading")
    assert "lifecycleState" not in data["project"]
    assert "lastLifecycleOperationId" not in data["project"]
    assert "lastLifecycleOperationType" not in data["project"]
    assert context["can_start_vm"] is True
