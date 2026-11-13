from django.http import HttpRequest

from lab.models import Run

from .employer_workflow import (
    get_employer_completion_url,
    get_incomplete_participation_for_user,
)


def get_required_employer_completion_url(
    request: HttpRequest, view_kwargs: dict
) -> str | None:
    """The employer form a signed-in user must complete before reaching this
    project page or API, if any. Enforced by AccountGatesMiddleware."""
    resolver_match = request.resolver_match
    if (
        not resolver_match
        or resolver_match.url_name == "participation_employer_completion"
    ):
        return None

    project_id = _get_project_id(resolver_match, view_kwargs)
    if not project_id or not get_incomplete_participation_for_user(
        request.user, project_id
    ):
        return None
    return get_employer_completion_url(project_id)


def _get_project_id(resolver_match, view_kwargs) -> int | None:
    if "project_id" in view_kwargs:
        return view_kwargs["project_id"]

    if resolver_match.url_name == "lab_project_change":
        return _parse_admin_object_id(view_kwargs.get("object_id"))

    if resolver_match.url_name == "lab_run_change":
        object_id = _parse_admin_object_id(view_kwargs.get("object_id"))
        if object_id is None:
            return None
        return (
            Run.objects.filter(id=object_id)
            .values_list("project_id", flat=True)
            .first()
        )

    return None


def _parse_admin_object_id(object_id) -> int | None:
    try:
        return int(object_id)
    except (TypeError, ValueError):
        return None
