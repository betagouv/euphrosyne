from django.urls import path

from .jwt.api_views import SessionAccessTokenView

urlpatterns = [
    path(
        "token/",
        SessionAccessTokenView.as_view(),
        name="token_obtain",
    ),
]
