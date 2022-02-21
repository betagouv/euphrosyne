from django import template
from django.contrib.admin.templatetags.admin_list import result_list
from django.contrib.admin.templatetags.base import InclusionAdminNode
from django.contrib.admin.utils import display_for_field
from django.utils.html import format_html

from ..models import Project

register = template.Library()


def project_results(
    list_display_status_index: int,
    _result_list: list[Project],
    results: list[list[str]],
):
    def update_result(project: Project, result: list[str]) -> list[str]:
        choice_identifier = Project.Status.names[
            Project.Status.values.index(project.status)
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

    return [
        update_result(_project, _result)
        for _project, _result in zip(_result_list, results)
    ]


def project_result_list(changelist):
    result_list_dict = result_list(changelist)
    result_list_dict["results"] = project_results(
        changelist.list_display.index("status"),
        changelist.result_list,
        result_list_dict["results"],
    )
    return result_list_dict


@register.tag(name="project_result_list")
def project_result_list_tag(parser, token):
    return InclusionAdminNode(
        parser,
        token,
        func=project_result_list,
        template_name="change_list_results.html",
        takes_context=False,
    )
