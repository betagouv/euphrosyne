import json

from django import template
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from lab.models import Project

register = template.Library()


@register.inclusion_tag("project_tabs.html")
def project_tabs(project_id: int, request: HttpRequest):
    if project_id:
        return {
            "tabs": (
                {
                    "id": "basic-info-tab",
                    "name": _("Basic information"),
                    "url": reverse("admin:lab_project_change", args=[project_id]),
                    "is_active": request.resolver_match.url_name
                    == "lab_project_change",
                },
                {
                    "id": "runs-tab",
                    "name": _("Run(s)"),
                    "url": (
                        reverse("admin:lab_run_changelist") + f"?project={project_id}"
                    ),
                    "is_active": request.resolver_match.url_name
                    in ["lab_run_changelist", "lab_run_change", "lab_run_add"],
                },
                {
                    "id": "documents-tab",
                    "name": _("Documents"),
                    "url": reverse("admin:lab_project_documents", args=[project_id]),
                    "is_active": request.resolver_match.url_name
                    == "lab_project_documents",
                },
                {
                    "id": "workplace-tab",
                    "name": _("Workplace"),
                    "url": reverse("admin:lab_project_workplace", args=[project_id]),
                    "is_active": request.resolver_match.url_name
                    == "lab_project_workplace",
                },
            )
        }
    return None


@register.inclusion_tag("components/header/project_header.html")
def project_header(project_id: int):
    if not project_id and not isinstance(project_id, int):
        return None

    project = Project.objects.get(pk=project_id)

    if not project:
        return None

    project_status = project.status
    choice_identifier = project_status.name
    class_name = choice_identifier.lower()

    return {
        "project": project,
        "status": {
            "class_name": class_name,
            "display": project_status.value[1],
        },
    }


@register.simple_tag
def project_header_json_data(project_id: int):
    if not project_id and not isinstance(project_id, int):
        return ""

    project = Project.objects.get(pk=project_id)

    if not project:
        return ""

    project_status = project.status
    choice_identifier = project_status.name
    class_name = choice_identifier.lower()

    data = {
        "backLink": {
            "href": reverse("admin:lab_project_changelist"),
            "title": str(_("Project")),
        },
        "project": {
            "name": project.name,
            "leader": project.leader.user.get_full_name()
            or project.leader.user.get_username(),
            "status": {"label": str(project_status.value[1]), "className": class_name},
        },
    }
    return json.dumps(data)
