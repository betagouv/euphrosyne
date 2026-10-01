from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_not_required
from django.db import models
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.urls.base import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic.edit import UpdateView
from social_django.models import Partial
from social_django.views import auth

from euphro_auth.models import User

from .invitations import (
    INVITATION_SESSION_KEY,
    registration_partial,
    reject_invitation,
    validated_invitation_user,
)


@never_cache
@login_not_required
@require_POST
def begin_registration(request: HttpRequest) -> HttpResponse:
    if validated_invitation_user(request) is None:
        return reject_invitation(request)
    # Let Social Auth create and validate the OAuth state; remember only which
    # generated attempt belongs to this validated invitation.
    request.session.pop("orcid_state", None)
    response = auth(request, backend="orcid")
    request.session[INVITATION_SESSION_KEY] = {
        **request.session[INVITATION_SESSION_KEY],
        "oauth_state": request.session["orcid_state"],
    }
    return response


class UserCompleteAccountView(UpdateView):
    """View displaying a form for the user to complete
    and verify his/her information in ORCID OAuth process.
    """

    template_name = "oauth_complete_information_form.html"
    model = get_user_model()
    fields = ["email", "first_name", "last_name"]
    registration_partial: Partial

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        saved = registration_partial(request, kwargs["token"])
        if saved is None or saved.kwargs["user"].invitation_completed_at:
            return reject_invitation(request)
        self.registration_partial = saved
        return super().dispatch(request, *args, **kwargs)

    def get_partial(self) -> Partial:
        return self.registration_partial

    def get_object(self, queryset: models.query.QuerySet | None = None) -> User:
        partial = self.get_partial()
        user = partial.kwargs.get("user")
        return user

    def get_initial(self) -> Dict[str, Any]:
        partial = self.get_partial()
        user_details = partial.kwargs.get("details")
        return {
            **super().get_initial(),
            "email": user_details.get("email", None) or self.object.email,
            "first_name": user_details.get("first_name", None),
            "last_name": user_details.get("last_name", None),
        }

    def form_valid(self, form: ModelForm) -> HttpResponse:
        self.object.invitation_completed_at = timezone.now()
        self.object.is_staff = True
        response = super().form_valid(form)
        return response

    def get_success_url(self) -> str:
        partial = self.get_partial()
        return reverse("social:complete", args=(partial.backend,))
