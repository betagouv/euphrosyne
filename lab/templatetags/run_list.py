from django import template

from ..admin.run_actions import get_change_state_text
from ..permissions import is_lab_admin

register = template.Library()


@register.inclusion_tag("admin/lab/run/run_list.html")
def show_run_list(request, change_list):
    result_list = change_list.result_list
    for result in result_list:
        result.change_state_action_name = get_change_state_text(
            is_lab_admin(request.user), result
        )
    return {"runs": result_list, "project_id": request.GET.get("project")}
