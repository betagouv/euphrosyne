from allauth.account import urls as allauth_account_urls
from allauth.mfa.base import views as mfa_views
from django.urls import URLPattern, path
from django.views.generic import RedirectView

from .mfa import views as euphro_mfa_views

# allauth account pages offered by the platform. Email management and setting a
# password without the current one are not offered; signup stays closed (see
# AccountAdapter) but its page is reversed by allauth's login view.
ACCOUNT_URL_NAMES = {
    "account_login",
    "account_logout",
    "account_inactive",
    "account_signup",
    "account_reauthenticate",
    "account_change_password",
    "account_reset_password",
    "account_reset_password_done",
    "account_reset_password_from_key",
    "account_reset_password_from_key_done",
}

urlpatterns: list[URLPattern] = [
    pattern
    for pattern in allauth_account_urls.urlpatterns
    if isinstance(pattern, URLPattern) and pattern.name in ACCOUNT_URL_NAMES
] + [
    # Reversed by allauth's password change view for accounts without a usable
    # password (ORCID-only accounts).
    path(
        "password/set/",
        RedirectView.as_view(url="/"),
        name="account_set_password",
    ),
    # Multi-factor authentication: TOTP only, no recovery codes.
    path("2fa/", euphro_mfa_views.IndexView.as_view(), name="mfa_index"),
    path("2fa/authenticate/", mfa_views.authenticate, name="mfa_authenticate"),
    path(
        "2fa/reauthenticate/",
        euphro_mfa_views.ReauthenticateView.as_view(),
        name="mfa_reauthenticate",
    ),
    path(
        "2fa/totp/activate/",
        euphro_mfa_views.ActivateTOTPView.as_view(),
        name="mfa_activate_totp",
    ),
    path(
        "2fa/totp/deactivate/",
        euphro_mfa_views.DeactivateTOTPView.as_view(),
        name="mfa_deactivate_totp",
    ),
]
