from allauth.idp.oidc.models import Client
from allauth.idp.oidc.views import DeviceAuthorizationView
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from lab.permissions import is_lab_admin


class EuphroDeviceAuthorizationView(DeviceAuthorizationView):
    """Page where a user approves a device (Herma) by entering its code.

    - Clients of OIDC_ADMIN_ONLY_CLIENTS can only be approved by lab
      administrators. AccountGatesMiddleware runs before this view, so their
      second factor is verified.
    - allauth exempts this view from CSRF checks: the approval form would then
      be accepted from another site. Overriding ``dispatch`` drops the
      exemption, so the confirm form carries a CSRF token.
    """

    # Not useless: a new ``dispatch`` has no ``csrf_exempt`` attribute.
    def dispatch(  # pylint: disable=useless-parent-delegation
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    def _dispatch_authorization(
        self, request: HttpRequest, user_code: str, device_code: str, client: Client
    ) -> HttpResponse:
        if client.id in settings.OIDC_ADMIN_ONLY_CLIENTS and not is_lab_admin(
            request.user
        ):
            raise PermissionDenied
        return super()._dispatch_authorization(request, user_code, device_code, client)


device_authorization = EuphroDeviceAuthorizationView.as_view()
