from django.urls import path

from .jwt.api_views import MFAEnforcingTokenRefreshView, SessionAccessTokenView

urlpatterns = [
    path(
        "token/",
        SessionAccessTokenView.as_view(),
        name="token_obtain",
    ),
    path(
        "token/refresh/", MFAEnforcingTokenRefreshView.as_view(), name="token_refresh"
    ),
]
