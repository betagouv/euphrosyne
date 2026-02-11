from django.urls import path

from . import api_views

app_name = "data_management"

urlpatterns = (
    path(
        "operations/callback",
        api_views.LifecycleOperationCallbackAPIView.as_view(),
        name="operations-callback",
    ),
)
