from unittest.mock import MagicMock

import pytest
from django.test import RequestFactory

from data_management.models import LifecycleState, ProjectData
from euphro_auth.tests.factories import StaffUserFactory
from lab.templatetags.run_list import show_run_list
from lab.tests.factories import RunFactory


@pytest.mark.django_db
def test_show_run_list_allows_create_run_when_project_is_hot():
    run = RunFactory()
    request = RequestFactory().get("/lab/run/", {"project": run.project_id})
    request.user = StaffUserFactory()

    context = show_run_list(request, MagicMock(result_list=[run]), run.project)

    assert context["can_create_run"] is True


@pytest.mark.django_db
def test_show_run_list_disables_create_run_when_project_is_immutable():
    run = RunFactory()
    project_data = ProjectData.for_project(run.project)
    project_data.lifecycle_state = LifecycleState.COOL
    project_data.save(update_fields=["lifecycle_state"])
    request = RequestFactory().get("/lab/run/", {"project": run.project_id})
    request.user = StaffUserFactory()

    context = show_run_list(request, MagicMock(result_list=[run]), run.project)

    assert context["can_create_run"] is False
