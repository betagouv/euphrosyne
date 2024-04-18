from itertools import groupby
from typing import Any, Callable

from django import template
from django.contrib.admin.templatetags.admin_list import (
    ResultList,
    items_for_result,
    result_list,
)
from django.contrib.admin.templatetags.base import InclusionAdminNode
from django.contrib.admin.views.main import ChangeList
from django.db.models.functions import TruncMonth
from django.db.models.query import QuerySet
from django.utils.html import format_html

from lab.models.project import ProjectQuerySet

from ..models import Project

register = template.Library()


def _get_status_cell(project: Project) -> str:
    project_status = project.status
    choice_identifier = project_status.name
    class_name = choice_identifier.lower()
    return format_html(
        '<td class="field-status">'
        '<span class="fr-tag fr-tag--sm {}">'
        "{}"
        "</span></td>",
        class_name,
        project_status.value[1],
    )


def _get_admin_cell(project: Project) -> str:
    admin_text = project.admin.get_full_name() if project.admin else ""
    return format_html('<td class="field-admin">{}</td>', admin_text)


def _get_leader_cell(project: Project) -> str:
    leader_text = project.leader.user.get_full_name() if project.leader else ""
    return format_html('<td class="field-leader">{}</td>', leader_text)


def update_result(
    changelist: ChangeList, project: Project, result: list[str]
) -> list[str]:
    status_index = changelist.list_display.index("status")
    admin_index = changelist.list_display.index("admin")
    leader_index = changelist.list_display.index("leader_user")

    result[status_index] = _get_status_cell(project)
    result[admin_index] = _get_admin_cell(project)
    result[leader_index] = _get_leader_cell(project)
    return result


def project_results(
    changelist: ChangeList,
    results: list[list[str]],
    project_list_results: list[Project] | ProjectQuerySet | None = None,
):
    if not project_list_results:
        project_list_results = changelist.result_list
    return [
        update_result(changelist, _project, _result)
        for _project, _result in zip(project_list_results, results)
    ]


@register.tag(name="project_result_list")
def project_result_list_tag(parser, token):
    return InclusionAdminNode(
        parser,
        token,
        func=project_result_list,
        template_name="change_list_results.html",
        takes_context=False,
    )


def project_result_list(
    changelist: ChangeList, queryset: QuerySet = None, regroup: bool = False
):
    """
    Updates the result list of the given ChangeList object
    based on the provided queryset or pagination settings.

    Args:
        changelist (ChangeList): The ChangeList object representing the list of results.
        queryset (QuerySet, optional): The queryset to be used as the result list.
            Defaults to None.
        regroup (bool, optional): Flag indicating whether to regroup the results.
            Defaults to False.

    Returns:
        dict: A dictionary containing the updated result list to be used in template.
    """
    if queryset is not None:
        changelist.result_list = queryset
    else:
        not_paginated = (
            changelist.show_all and changelist.can_show_all
        ) or not changelist.multi_page
        if not_paginated:
            changelist.result_list = (
                changelist.queryset._clone()  # pylint: disable=protected-access
            )
        else:
            changelist.result_list = changelist.paginator.page(
                changelist.page_num
            ).object_list

    result_list_dict = result_list(changelist)
    result_list_dict["results"] = project_results(
        changelist=changelist,
        results=result_list_dict["results"],
    )
    if regroup:
        result_list_dict["do_regroup"] = regroup
        result_list_dict["grouped_results"] = group_results_by_month(changelist)
    return result_list_dict


def group_results_by_month(changelist: ChangeList):
    changelist.result_list = changelist.result_list.annotate(
        month=TruncMonth("first_run_date")
    )
    return _group_results(changelist, attr_getter_fn=lambda p: p.month)


def _group_results(changelist: ChangeList, attr_getter_fn: Callable[[Project], Any]):
    """
    Group the results from a ChangeList based on a specific attribute.

    This function sorts the results in the ChangeList in descending order
    based on the attribute specified by attr_getter_fn.
    It then groups the results by this attribute and yields each group along with
    a list of ResultList objects for the results in that group.

    Args:
        changelist (ChangeList): The ChangeList to group.
        attr_getter_fn (str): The function to use to get the
            attribute to sort & group by.

    Yields:
        tuple: A tuple containing the group and a list of ResultList objects
            for that group.
    """
    grouped_results = groupby(
        sorted(changelist.result_list, key=attr_getter_fn, reverse=True),
        attr_getter_fn,
    )

    for group, result_grouper in grouped_results:
        results = list(result_grouper)
        yield (
            group,
            project_results(
                changelist,
                results=[
                    update_result(
                        changelist,
                        result,
                        ResultList(None, items_for_result(changelist, result, None)),
                    )
                    for result in results
                ],
                project_list_results=results,
            ),
        )
