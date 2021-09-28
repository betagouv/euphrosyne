from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView

from .forms import ProfileRegistrationForm
from .models import Profile


class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Profile
    form_class = ProfileRegistrationForm
    template_name = "registration_profile.html"
    success_url = "/"

    def get_form_kwargs(self) -> Dict[str, Any]:
        return {**super().get_form_kwargs(), "user": self.request.user}
