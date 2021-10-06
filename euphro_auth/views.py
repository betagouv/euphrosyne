from typing import Any, Dict

from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .forms import UserInvitationRegistrationForm


class UserTokenRegistrationView(PasswordResetConfirmView):
    title = _("Enter your information")
    form_class = UserInvitationRegistrationForm
    template_name = "euphro_invitation_registration_form.html"
    success_url = reverse_lazy("admin:index")
    post_reset_login = True

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if self.user:
            initial["email"] = self.user.email
        return initial
