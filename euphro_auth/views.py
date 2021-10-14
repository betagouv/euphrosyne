from typing import Any, Dict

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.http.response import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from .emails import send_invitation_email
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


class SendAnEmailView(View):
    def get(self, request, *args, **kwargs):
        token = default_token_generator.make_token(request.user)
        ret = send_invitation_email(
            email=request.user.email, user_id=request.user.pk, token=token
        )
        return HttpResponse(ret)
