from django.http import JsonResponse
from django.shortcuts import redirect

from lab.models import Run

from .employer_workflow import (
    get_employer_completion_url,
    get_incomplete_participation_for_user,
)


class ParticipationEmployerCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(
        self,
        request,
        view_func,  # pylint: disable=unused-argument
        view_args,  # pylint: disable=unused-argument
        view_kwargs,
    ):
        if not request.user.is_authenticated:
            return None

        resolver_match = request.resolver_match
        if (
            not resolver_match
            or resolver_match.url_name == "participation_employer_completion"
        ):
            return None

        project_id = self._get_project_id(resolver_match, view_kwargs)

        if not project_id or not get_incomplete_participation_for_user(
            request.user, project_id
        ):
            return None

        completion_url = get_employer_completion_url(project_id)
        if resolver_match.namespace == "api" or request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "detail": "Employer information is required for this project.",
                    "completion_url": completion_url,
                },
                status=403,
            )
        return redirect(completion_url)

    @staticmethod
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
