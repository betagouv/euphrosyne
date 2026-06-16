import json

import pytest
from django.test import RequestFactory

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from lab.tests.factories import RunFactory
from lab_notebook.views import NotebookView


@pytest.mark.django_db
def test_notebook_view_exposes_hdf5_generation_flags_for_lab_admin():
    run = RunFactory()
    request = RequestFactory().get(f"/lab/run/{run.id}/notebook")
    request.user = LabAdminUserFactory()
    view = NotebookView()
    view.request = request
    view.run = run

    context = view.get_context_data()
    data = json.loads(context["json_data"])

    assert data["isLabAdmin"] is True
    assert data["canWriteNotebook"] is True
    assert data["canGenerateNotebookFromHDF5"] is True


@pytest.mark.django_db
def test_notebook_view_disables_hdf5_generation_for_non_lab_admin():
    run = RunFactory()
    request = RequestFactory().get(f"/lab/run/{run.id}/notebook")
    request.user = StaffUserFactory()
    view = NotebookView()
    view.request = request
    view.run = run

    context = view.get_context_data()
    data = json.loads(context["json_data"])

    assert data["isLabAdmin"] is False
    assert data["canWriteNotebook"] is True
    assert data["canGenerateNotebookFromHDF5"] is False


@pytest.mark.django_db
def test_notebook_view_disables_hdf5_generation_when_project_is_immutable(
    monkeypatch,
):
    run = RunFactory()
    request = RequestFactory().get(f"/lab/run/{run.id}/notebook")
    request.user = LabAdminUserFactory()
    view = NotebookView()
    view.request = request
    view.run = run
    monkeypatch.setattr("lab_notebook.views.is_project_data_immutable", lambda _: True)

    context = view.get_context_data()
    data = json.loads(context["json_data"])

    assert data["isLabAdmin"] is True
    assert data["canWriteNotebook"] is False
    assert data["canGenerateNotebookFromHDF5"] is False
