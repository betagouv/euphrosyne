from django.urls import path

from . import api_views

urlpatterns = (
    path(
        "",
        api_views.DataRequestCreateAPIView.as_view(),
        name="create",
    ),
    path(
        "access-event",
        api_views.DataAccessEventCreateAPIView.as_view(),
        name="create-access-event",
    ),
)
