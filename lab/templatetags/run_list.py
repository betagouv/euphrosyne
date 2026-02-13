from typing import Any

from django import template
from django.contrib.admin.views.main import ChangeList
from django.http import HttpRequest

from ..permissions import is_lab_admin
from ..project_immutability import is_project_data_immutable
from ..projects.models import Project
from ..runs.admin_actions import get_change_state_text

register = template.Library()


@register.inclusion_tag("admin/lab/run/run_list.html")
def show_run_list(
    request: HttpRequest,
    change_list: ChangeList,
    project: Project | None = None,
) -> dict[str, Any]:
    result_list = change_list.result_list
    project_id = request.GET.get("project")
    can_create_run = True if project is None else not is_project_data_immutable(project)
    for result in result_list:
        result.change_state_action_name = get_change_state_text(
            is_lab_admin(request.user), result
        )
    return {
        "runs": result_list,
        "project_id": project_id,
        "can_create_run": can_create_run,
    }
