from django import template
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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
            )
        }
    return None
