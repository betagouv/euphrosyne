from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from lab.models import Project

from .employer_workflow import get_incomplete_participation_for_user
from .forms import EmployerCompletionForm
from .models import Employer


def _get_previous_employer_initial(participation):
    previous_participation = (
        participation.user.participation_set.filter(
            institution=participation.institution,
            employer__isnull=False,
        )
        .exclude(id=participation.id)
        .select_related("employer")
        .order_by("-created")
        .first()
    )
    if not previous_participation or not previous_participation.employer:
        return None
    employer = previous_participation.employer
    return {
        "email": employer.email,
        "first_name": employer.first_name,
        "last_name": employer.last_name,
        "function": employer.function,
    }


@login_required
def complete_employer_information(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)
    participation = get_incomplete_participation_for_user(request.user, project_id)
    project_url = reverse("admin:lab_project_change", args=[project_id])

    if participation is None:
        if project.participation_set.filter(user=request.user).exists() or getattr(
            request.user, "is_lab_admin", False
        ):
            return redirect(project_url)
        raise Http404

    form = EmployerCompletionForm(
        request.POST or None,
        initial=_get_previous_employer_initial(participation),
    )
    if request.method == "POST" and form.is_valid():
        employer = Employer.objects.create(**form.cleaned_data)
        participation.employer = employer
        participation.save(update_fields=["employer", "modified"])
        messages.success(request, _("Employer information has been saved."))
        return redirect(project_url)

    return render(
        request,
        "lab/participations/employer_completion.html",
        {
            "form": form,
            "participation": participation,
            "project": project,
            "title": _("Employer information required"),
        },
    )
