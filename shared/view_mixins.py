from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse


class StaffUserRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_staff:
            return self.handle_no_permission()
        return response
