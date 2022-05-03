from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .jwt.api_views import SessionTokenObtainPairView

urlpatterns = [
    path(
        "token/",
        SessionTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
