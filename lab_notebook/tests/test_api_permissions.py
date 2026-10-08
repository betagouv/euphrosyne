from unittest import mock

import pytest
from django.core.exceptions import PermissionDenied

from lab.tests import factories
from lab_notebook.api.run.views import RunNotebookView


@pytest.mark.parametrize("method", ["put", "patch"])
def test_notebook_update_permissions(project_api_context, method):
    context = project_api_context
    response = getattr(context.client, method)(
        f"/api/notebook/run-notebook/{context.run.id}",
        {"comments": "Updated comments"},
        content_type="application/json",
    )
    assert response.status_code == (200 if context.can_access_project else 403)
    context.run.run_notebook.refresh_from_db()
    assert context.run.run_notebook.comments == (
        "Updated comments" if context.can_access_project else ""
    )


@pytest.mark.django_db
def test_notebook_get_object_checks_permissions():
    run = factories.RunFactory()
    view = RunNotebookView()
    view.kwargs = {"run_id": run.id}
    view.request = mock.sentinel.request
    with mock.patch.object(
        view, "check_object_permissions", side_effect=PermissionDenied
    ) as permission_check:
        with pytest.raises(PermissionDenied):
            view.get_object()
    permission_check.assert_called_once_with(view.request, run.run_notebook)
