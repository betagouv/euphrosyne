from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.utils.decorators import method_decorator


class StaffUserRequiredMixin(LoginRequiredMixin):
    @method_decorator(staff_member_required)
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
