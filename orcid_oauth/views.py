from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.forms.models import ModelForm
from django.http.response import HttpResponse
from django.urls.base import reverse
from django.views.generic.edit import UpdateView
from social_django.models import Partial
from social_django.utils import load_strategy

from euphro_auth.models import User


class UserCompleteAccountView(UpdateView):
    """View displaying a form for the user to complete
    and verify his/her information in ORCID OAuth process.
    """

    template_name = "oauth_complete_information_form.html"
    model = get_user_model()
    fields = ["email", "first_name", "last_name"]

    def get_partial(self) -> Partial:
        strategy = load_strategy()
        partial_token = self.kwargs.get("token")
        return strategy.partial_load(partial_token)

    def get_object(self, queryset: Optional[models.query.QuerySet] = ...) -> User:
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
        self.object.invitation_completed = True
        response = super().form_valid(form)
        return response

    def get_success_url(self) -> str:
        partial = self.get_partial()
        return reverse("social:complete", args=(partial.backend,))
