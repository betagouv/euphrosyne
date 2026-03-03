from django.urls import path

from . import api_views

app_name = "data_management"

urlpatterns = (
    path(
        "projects/<int:project_id>/restore",
        api_views.ProjectRestoreTriggerAPIView.as_view(),
        name="project-restore",
    ),
    path(
        "operations/callback",
        api_views.LifecycleOperationCallbackAPIView.as_view(),
        name="operations-callback",
    ),
)
