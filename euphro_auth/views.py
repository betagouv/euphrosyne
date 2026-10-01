from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import (
    INTERNAL_RESET_SESSION_TOKEN,
    PasswordResetConfirmView,
)
from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from social_django.views import auth as social_auth

from orcid_oauth.invitations import (
    INVITATION_SESSION_KEY,
    clear_invitation,
    reject_invitation,
    store_invitation,
    validated_invitation_user,
)

from .forms import CGUAcceptanceForm, UserInvitationRegistrationForm


class UserTokenRegistrationView(PasswordResetConfirmView):
    title = _("Enter your information")
    form_class = UserInvitationRegistrationForm
    template_name = "euphro_invitation_registration_form.html"
    success_url = reverse_lazy("admin:index")
    post_reset_login = True
    reset_url_token = "registration"
    post_reset_login_backend = "euphro_auth.backends.LowercaseEmailBackend"

    def dispatch(self, *args: Any, **kwargs: Any) -> HttpResponseBase:
        request = self.request
        # get_user decodes the URL's UID on the server; the same token validator
        # as the classic invitation flow must approve it before we store a target.
        user = self.get_user(kwargs["uidb64"])
        token = kwargs["token"]
        if token != self.reset_url_token:
            clear_invitation(request)
            if user is not None:
                store_invitation(request, user, token)
        elif user is None or not self.token_generator.check_token(
            user, request.session.get(INTERNAL_RESET_SESSION_TOKEN)
        ):
            clear_invitation(request)
        return super().dispatch(*args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.POST.get("provider") != "orcid":
            return super().post(request, *args, **kwargs)
        target = validated_invitation_user(request)
        if target is None or self.user is None or target.pk != self.user.pk:
            return reject_invitation(request)
        # Django's invitation dispatch has already validated this page's token.
        # Let Social Auth create the state and bind its attempt to that target.
        request.session.pop("orcid_state", None)
        response = social_auth(request, backend="orcid")
        request.session[INVITATION_SESSION_KEY] = {
            **request.session[INVITATION_SESSION_KEY],
            "oauth_state": request.session["orcid_state"],
        }
        return response

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.user:
            initial["email"] = self.user.email
        return initial

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        target = validated_invitation_user(self.request)
        context["orcid_registration_available"] = bool(
            self.validlink and target and self.user and target.pk == self.user.pk
        )
        return context

    def form_valid(self, form: SetPasswordForm) -> HttpResponse:
        clear_invitation(self.request)
        return super().form_valid(form)


@login_required
def cgu_acceptance_view(request):
    if request.method == "POST":
        form = CGUAcceptanceForm(request.POST)
        if form.is_valid():
            request.user.cgu_accepted_at = timezone.now()
            request.user.save()
            return redirect("/")
        messages.error(
            request, _("You must accept the Terms and Conditions to continue.")
        )

    else:
        form = CGUAcceptanceForm()

    return render(
        request,
        "euphro_auth/cgu_acceptance.html",
        context={
            "title": _("Terms and Conditions Agreement"),
            "site_title": "Euphrosyne",
            "form": form,
        },
    )
