from typing import Any, Dict

from allauth.account.internal.flows.login import record_authentication
from allauth.account.utils import perform_login
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.db import models
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.utils import timezone
from django.views.generic.edit import UpdateView

from euphro_auth.models import User

from .completion import clear_completion, pending_completion
from .invitations import reject_invitation


class UserCompleteAccountView(UpdateView):
    """View displaying a form for the user to complete
    and verify his/her information after the first ORCID sign-in.
    """

    template_name = "oauth_complete_information_form.html"
    model = get_user_model()
    fields = ["email", "first_name", "last_name"]
    user: User
    account: SocialAccount
    details: dict[str, str]

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        pending = pending_completion(request, kwargs["token"])
        if pending is None:
            clear_completion(request)
            return reject_invitation(request)
        self.user, self.account, self.details = pending
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset: models.query.QuerySet | None = None) -> User:
        return self.user

    def get_initial(self) -> Dict[str, Any]:
        return {**super().get_initial(), **self.details}

    def form_valid(self, form: ModelForm) -> HttpResponse:
        self.object.invitation_completed_at = timezone.now()
        self.object.is_staff = True
        form.save()
        clear_completion(self.request)
        record_authentication(
            self.request,
            self.object,
            "socialaccount",
            provider=self.account.provider,
            uid=self.account.uid,
        )
        return perform_login(self.request, self.object, redirect_url="/")
