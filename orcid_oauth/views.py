from typing import Any, Dict, cast

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.forms.models import ModelForm
from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic.edit import UpdateView

from euphro_auth.models import User


def is_completion_required(user: User) -> bool:
    """An invited user who signed in with ORCID completes their information
    before using the platform (see euphro_auth's AccountGatesMiddleware)."""
    return (
        user.invitation_completed_at is None
        and SocialAccount.objects.filter(user=user, provider="orcid").exists()
    )


class UserCompleteAccountView(LoginRequiredMixin, UpdateView):
    """View displaying a form for the user to complete
    and verify his/her information after the first ORCID sign-in.
    """

    template_name = "oauth_complete_information_form.html"
    model = User
    fields = ["email", "first_name", "last_name"]
    success_url = "/"

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if request.user.is_authenticated and not is_completion_required(
            cast(User, request.user)
        ):
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset: models.query.QuerySet | None = None) -> User:
        return cast(User, self.request.user)

    def get_initial(self) -> Dict[str, Any]:
        account = SocialAccount.objects.get(user=self.object, provider="orcid")
        # Values returned by ORCID, which the form proposes.
        proposed = account.get_provider().extract_common_fields(account.extra_data)
        return {
            **super().get_initial(),
            **{
                field: value
                for field, value in proposed.items()
                if field in self.fields and value
            },
        }

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.invitation_completed_at = timezone.now()
        form.instance.is_staff = True
        return super().form_valid(form)
