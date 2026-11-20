from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .jwt.api_views import SessionAccessTokenView

urlpatterns = [
    path(
        "token/",
        SessionAccessTokenView.as_view(),
        name="token_obtain",
    ),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
