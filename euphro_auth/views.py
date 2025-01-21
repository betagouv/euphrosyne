from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .forms import CGUAcceptanceForm, UserInvitationRegistrationForm


class UserTokenRegistrationView(PasswordResetConfirmView):
    title = _("Enter your information")
    form_class = UserInvitationRegistrationForm
    template_name = "euphro_invitation_registration_form.html"
    success_url = reverse_lazy("admin:index")
    post_reset_login = True
    reset_url_token = "registration"
    post_reset_login_backend = "django.contrib.auth.backends.ModelBackend"

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.user:
            initial["email"] = self.user.email
        return initial

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context.update({"user_id": self.user.id})
        return context


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
