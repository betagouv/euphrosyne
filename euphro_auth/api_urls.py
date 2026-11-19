from django.urls import path

from .jwt.api_views import (
    MFAEnforcingTokenRefreshView,
    SessionTokenObtainPairView,
)

urlpatterns = [
    path(
        "token/",
        SessionTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/", MFAEnforcingTokenRefreshView.as_view(), name="token_refresh"
    ),
]
