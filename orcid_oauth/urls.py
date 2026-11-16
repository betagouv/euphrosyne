from allauth.socialaccount import views as socialaccount_views
from allauth.socialaccount.providers.orcid import views as orcid_views
from django.urls import path

from .views import UserCompleteAccountView

urlpatterns = [
    path("accounts/orcid/login/", orcid_views.oauth2_login, name="orcid_login"),
    # The redirect URI registered with ORCID.
    path("complete/orcid/", orcid_views.oauth2_callback, name="orcid_callback"),
    path(
        "accounts/3rdparty/login/cancelled/",
        socialaccount_views.login_cancelled,
        name="socialaccount_login_cancelled",
    ),
    path(
        "registration/orcid/complete/",
        UserCompleteAccountView.as_view(),
        name="complete_registration_orcid",
    ),
]
