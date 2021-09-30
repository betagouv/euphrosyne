from typing import Any, Dict

from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetConfirmView
from django.http.response import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .forms import UserInvitationRegistrationForm


class UserTokenRegistrationView(
    PasswordResetConfirmView
):  # pylint: disable=too-many-ancestors
    title = _("Enter your information")
    form_class = UserInvitationRegistrationForm
    template_name = "euphro_invitation_registration_form.html"
    success_url = reverse_lazy("admin:index")

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.user:
            initial["email"] = self.user.email
        return initial

    def form_valid(self, form) -> HttpResponse:
        response = super().form_valid(form)
        login(self.request, self.user)
        return response
