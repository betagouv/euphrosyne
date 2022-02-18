from django import template
from django.contrib.admin.templatetags.admin_list import result_list
from django.contrib.admin.templatetags.base import InclusionAdminNode
from django.contrib.admin.utils import display_for_field
from django.utils.html import format_html

from ..models import Project
from ..models.project import ProjectStatus

register = template.Library()


def custom_result_list(changelist):
    result_list_dict = result_list(changelist)
    _results = result_list_dict["results"]

    list_display_status_index = changelist.list_display.index("status")

    def update_result(project: Project, result: list[str]) -> list[str]:
        choice_identifier = ProjectStatus.names[
            ProjectStatus.values.index(project.status)
        ]
        class_name = choice_identifier.lower()
        display = display_for_field(1, project._meta.get_field("status"), "")
        result[list_display_status_index] = format_html(
            '<td class="field-status">'
            f'<span class="fr-tag {class_name}">'
            f"{display}"
            "</span>"
            "</td>"
        )
        return result

    custom_results = [
        update_result(_project, _result)
        for _project, _result in zip(changelist.result_list, _results)
    ]

    result_list_dict["results"] = custom_results
    return result_list_dict


@register.tag(name="project_result_list")
def project_result_list_tag(parser, token):
    return InclusionAdminNode(
        parser,
        token,
        func=custom_result_list,
        template_name="change_list_results.html",
        takes_context=False,
    )
