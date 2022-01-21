import json
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test.client import RequestFactory
from django.urls import reverse

from ...models import Project
from ...views import change_leader_view
from .. import factories


@mock.patch.object(change_leader_view.ChangeLeaderView, "_process_request", mock.Mock())
@mock.patch.object(change_leader_view, "is_lab_admin", mock.Mock(return_value=True))
def test_change_leader_as_admin_is_allowed():
    request = RequestFactory().post(
        reverse("admin:lab_project_leader_participation_change", args=[1]),
        data={"leader_participation": 42},
    )
    request.user = mock.Mock()

    # Should not raise PermissionDenied:
    change_leader_view.ChangeLeaderView().dispatch(request, 1)


@mock.patch.object(change_leader_view, "is_lab_admin", mock.Mock(return_value=False))
def test_change_leader_as_non_admin_is_forbidden():
    request = RequestFactory().post(
        reverse("admin:lab_project_leader_participation_change", args=[1]),
        data={"leader_participation": 42},
    )
    request.user = mock.Mock()

    with pytest.raises(PermissionDenied):
        change_leader_view.ChangeLeaderView().dispatch(request, 1)


@pytest.mark.django_db
def test_update_participation():
    project = factories.ProjectWithMultipleParticipationsFactory()
    old_leader = project.participation_set.filter(is_leader=True).get()
    new_leader = project.participation_set.filter(is_leader=False)[0]
    change_leader_view.ChangeLeaderView._update_participation(  # pylint: disable=protected-access
        project, new_leader.id
    )
    new_leader.refresh_from_db()
    old_leader.refresh_from_db()
    assert new_leader.is_leader
    assert not old_leader.is_leader


@mock.patch.object(change_leader_view.transaction, "atomic", mock.MagicMock())
@mock.patch.object(change_leader_view.Project, "leader", mock.Mock())
@mock.patch.object(change_leader_view.ChangeLeaderForm, "full_clean", mock.Mock())
@mock.patch.object(change_leader_view.ChangeLeaderView, "_update_participation")
def test_change_leader_updates_participation(mocked_update_participation):
    project = Project(id=1)
    form = change_leader_view.ChangeLeaderView.form_class(
        project=project, data={"leader_participation": 42}
    )
    form.cleaned_data = {"leader_participation": mock.Mock(id=42)}
    view = change_leader_view.ChangeLeaderView()
    view.project = project
    view.request = RequestFactory().post(
        reverse("admin:lab_project_leader_participation_change", args=[1]),
        data={"leader_participation": 42},
    )

    view.form_valid(form)

    mocked_update_participation.assert_called_with(project, 42)


@mock.patch.object(change_leader_view.transaction, "atomic", mock.MagicMock())
@mock.patch.object(change_leader_view.Project, "leader", mock.Mock())
@mock.patch.object(change_leader_view.ChangeLeaderForm, "full_clean", mock.Mock())
@mock.patch.object(change_leader_view.ChangeLeaderView, "_update_participation")
@mock.patch.object(change_leader_view, "TemplateResponse")
def test_change_leader_in_popup_renders_json_object(
    template_response, mocked_update_participation
):
    project = Project(id=1)
    form = change_leader_view.ChangeLeaderView.form_class(
        project=project, data={"leader_participation": 42, "_popup": 1}
    )
    form.cleaned_data = {"leader_participation": mock.Mock(id=42)}
    view = change_leader_view.ChangeLeaderView()
    view.project = project
    view.request = RequestFactory().post(
        reverse("admin:lab_project_leader_participation_change", args=[1]),
        data={"leader_participation": 42, "_popup": 1},
    )
    mocked_update_participation.return_value.get.return_value.user = get_user_model()(
        id=1, first_name="Denis", last_name="Lamalice", email="d@m.com"
    )

    view.form_valid(form)

    template_response.assert_called_with(
        view.request,
        "admin/view_popup_response.html",
        {
            "popup_response_data": json.dumps(
                {
                    "action": "change",
                    "obj": "Lamalice, Denis<d@m.com>",
                    "new_value": "1",
                }
            )
        },
    )
