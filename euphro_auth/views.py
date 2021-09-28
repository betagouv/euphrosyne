from django.contrib.auth.views import PasswordResetConfirmView
from django.utils.translation import gettext_lazy as _


class UserTokenRegistrationView(
    PasswordResetConfirmView
):  # pylint: disable=too-many-ancestors
    title = _("Enter your information")
