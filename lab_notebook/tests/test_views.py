import json
from unittest import mock

import pytest
from django.test import RequestFactory
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from lab.tests.factories import RunFactory
from lab_notebook.views import NotebookView


def test_pdf_export_route_is_not_registered():
    with pytest.raises(NoReverseMatch):
        reverse("admin:lab_run_notebook_export_pdf", kwargs={"run_id": 1})
    with pytest.raises(Resolver404):
        resolve("/lab/run/1/notebook/export-pdf", urlconf="lab_notebook.urls")


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post"])
@mock.patch("requests.get")
@mock.patch("requests.post")
def test_removed_pdf_export_cannot_trigger_external_calls(
    mock_post, mock_get, project_api_context, method
):
    context = project_api_context
    is_staff = context.user is not None and context.user.is_staff
    path = f"/lab/run/{context.run.pk}/notebook/export-pdf"
    response = getattr(context.client, method)(path)
    if is_staff:
        # Unknown admin URLs fall through to the generic slash redirect.
        assert response.status_code == 301
        assert response.url == f"{path}/"
    else:
        # The admin catch-all sends unauthenticated/non-staff users to login.
        assert response.status_code == 302
        assert response.url.startswith("/login/")
    mock_get.assert_not_called()
    mock_post.assert_not_called()


@pytest.mark.django_db
def test_notebook_page_has_no_pdf_export_action(client):
    run = RunFactory()
    client.force_login(LabAdminUserFactory())
    response = client.get(reverse("admin:lab_run_notebook", kwargs={"run_id": run.pk}))
    assert response.status_code == 200
    assert response.context["run"] == run
    html = response.content.decode()
    assert "notebook/export-pdf" not in html
    assert 'id="notebook"' in html
    assert 'id="notebook-generation-action"' in html
    assert 'id="run-comment-textarea"' in html


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
    assert "canGenerateNotebookFromHDF5" not in data


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
    assert "canGenerateNotebookFromHDF5" not in data


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
    assert "canGenerateNotebookFromHDF5" not in data
