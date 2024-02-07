from unittest import mock

import pytest
from django.db.models.functions import TruncMonth
from django.utils import timezone

from ..models.project import Project
from ..templatetags.list_results import (
    _group_results,
    group_results_by_month,
    project_result_list,
    project_results,
)
from .factories import ProjectFactory, RunFactory


@pytest.mark.django_db
def test_custom_result_list():
    project = ProjectFactory()

    changelist = mock.MagicMock(list_display=["status", "admin", "leader_user"])

    print(
        project_results(
            changelist,
            [["old status repr", "old_admin_repr", "old_leader_user_repr"]],
            [project],
        )
    )

    assert project_results(
        changelist,
        [["old status repr", "old_admin_repr", "old_leader_user_repr"]],
        [project],
    ) == [
        [
            # pylint: disable=line-too-long
            '<td class="field-status"><span class="fr-tag fr-tag--sm to_schedule">A planifier</span></td>',
            '<td class="field-admin"></td>',
            '<td class="field-leader"></td>',
        ]
    ]


@pytest.mark.django_db
def test_group_results():
    class ResultListMock(mock.MagicMock):
        pass

    projects: list[Project] = [
        *ProjectFactory.create_batch(3),
        RunFactory(start_date=timezone.now() + timezone.timedelta(days=1)).project,
    ]

    with mock.patch(
        "lab.templatetags.list_results.ResultList", return_value=ResultListMock()
    ):
        changelist = mock.MagicMock(result_list=projects)
        results = list(_group_results(changelist, lambda p: p.status.value[1]))

    assert len(results) == 2
    assert results[0][0] == Project.Status.SCHEDULED.value[1]
    assert len(results[0][1]) == 1
    assert isinstance(results[0][1][0], ResultListMock)
    assert results[1][0] == Project.Status.TO_SCHEDULE.value[1]
    assert len(results[1][1]) == 3
    assert isinstance(results[1][1][0], ResultListMock)


def test_group_results_by_month():
    with mock.patch(
        "lab.templatetags.list_results._group_results"
    ) as _group_results_mock:
        result_list_mock = mock.MagicMock()
        changelist = mock.MagicMock()
        changelist.result_list = result_list_mock

        group_results_by_month(changelist)

        result_list_mock.annotate.assert_called_once_with(
            month=TruncMonth("first_run_date")
        )
        assert _group_results_mock.call_count == 1
        assert "attr_getter_fn" in _group_results_mock.call_args[1]
        assert (
            _group_results_mock.call_args[1]["attr_getter_fn"](mock.MagicMock(month=1))
            == 1
        )


@mock.patch("lab.templatetags.list_results.result_list")
@mock.patch("lab.templatetags.list_results.project_results", mock.MagicMock())
def test_project_result_list_when_passing_qs(result_list_mock: mock.MagicMock):
    passed_qs = mock.MagicMock()
    changelist = mock.MagicMock()
    project_result_list(changelist, queryset=passed_qs)

    assert result_list_mock.call_args[0][0].result_list == passed_qs
    changelist.paginator.page.assert_not_called()
    changelist.queryset._clone.assert_not_called()  # pylint: disable=protected-access


@mock.patch("lab.templatetags.list_results.result_list", mock.MagicMock())
@mock.patch("lab.templatetags.list_results.project_results", mock.MagicMock())
def test_project_result_list_when_paginated():
    changelist = mock.MagicMock(
        multi_page=True, page_num=1, show_all=False, can_show_all=True
    )
    project_result_list(changelist)

    changelist.paginator.page.assert_called_once()
    changelist.queryset._clone.assert_not_called()  # pylint: disable=protected-access


@mock.patch("lab.templatetags.list_results.result_list", mock.MagicMock())
@mock.patch("lab.templatetags.list_results.project_results", mock.MagicMock())
def test_project_result_list_when_not_paginated():
    changelist = mock.MagicMock(multi_page=False, show_all=True, can_show_all=True)
    project_result_list(changelist)

    changelist.paginator.page.assert_not_called()
    changelist.queryset._clone.assert_called_once()  # pylint: disable=protected-access


@mock.patch(
    "lab.templatetags.list_results.result_list",
    mock.MagicMock(return_value={"results": []}),
)
@mock.patch("lab.templatetags.list_results.project_results", mock.MagicMock())
@mock.patch("lab.templatetags.list_results.group_results_by_month", mock.MagicMock())
def test_project_result_list_when_regroup():
    changelist = mock.MagicMock()

    results = project_result_list(changelist, queryset=None, regroup=True)

    assert "grouped_results" in results
    assert results["do_regroup"] is True
