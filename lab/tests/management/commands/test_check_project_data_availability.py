import os
from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command

from data_management.models import LifecycleState
from lab.tests.factories import FinishedProject


def _available_response(*, available: bool) -> mock.Mock:
    response = mock.Mock(ok=True)
    response.json.return_value = {"available": available}
    return response


@pytest.mark.django_db
def test_check_project_data_availability_only_checks_hot_projects():
    hot_project = FinishedProject(is_data_available=False)
    cooling_project = FinishedProject(is_data_available=False)

    hot_project.project_data.lifecycle_state = LifecycleState.HOT
    hot_project.project_data.save(update_fields=["lifecycle_state"])
    cooling_project.project_data.lifecycle_state = LifecycleState.COOLING
    cooling_project.project_data.save(update_fields=["lifecycle_state"])

    with (
        mock.patch(
            "lab.management.commands.check_project_data_availability."
            "EuphroToolsAPIToken.for_euphrosyne"
        ) as token_mock,
        mock.patch(
            "lab.management.commands.check_project_data_availability.requests.get",
            return_value=_available_response(available=True),
        ) as get_mock,
    ):
        token_mock.return_value.access_token = "fake-token"

        call_command("check_project_data_availability", stdout=StringIO())

    hot_project.refresh_from_db()
    cooling_project.refresh_from_db()

    assert hot_project.is_data_available is True
    assert cooling_project.is_data_available is False
    get_mock.assert_called_once_with(
        os.environ["EUPHROSYNE_TOOLS_API_URL"] + f"/data/available/{hot_project.slug}",
        timeout=10,
        headers={"Authorization": "Bearer fake-token"},
    )


@pytest.mark.django_db
def test_check_project_data_availability_checks_all_projects_without_data_management():
    hot_project = FinishedProject(is_data_available=False)
    cool_project = FinishedProject(is_data_available=False)

    hot_project.project_data.lifecycle_state = LifecycleState.HOT
    hot_project.project_data.save(update_fields=["lifecycle_state"])
    cool_project.project_data.lifecycle_state = LifecycleState.COOL
    cool_project.project_data.save(update_fields=["lifecycle_state"])

    with (
        mock.patch(
            "lab.management.commands.check_project_data_availability."
            "EuphroToolsAPIToken.for_euphrosyne"
        ) as token_mock,
        mock.patch(
            "lab.management.commands.check_project_data_availability.apps.is_installed",
            return_value=False,
        ),
        mock.patch(
            "lab.management.commands.check_project_data_availability.requests.get",
            return_value=_available_response(available=False),
        ) as get_mock,
    ):
        token_mock.return_value.access_token = "fake-token"

        call_command("check_project_data_availability", stdout=StringIO())

    requested_urls = {call.args[0] for call in get_mock.call_args_list}

    assert get_mock.call_count == 2
    assert requested_urls == {
        os.environ["EUPHROSYNE_TOOLS_API_URL"] + f"/data/available/{hot_project.slug}",
        os.environ["EUPHROSYNE_TOOLS_API_URL"] + f"/data/available/{cool_project.slug}",
    }
    for call in get_mock.call_args_list:
        assert call.kwargs == {
            "timeout": 10,
            "headers": {"Authorization": "Bearer fake-token"},
        }
