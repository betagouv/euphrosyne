from django.urls import path

from . import api_views

app_name = "data_management"

urlpatterns = (
    path(
        "operations/<uuid:operation_id>",
        api_views.LifecycleOperationDetailAPIView.as_view(),
        name="operation-detail",
    ),
    path(
        "projects/<int:project_id>/restore",
        api_views.ProjectRestoreTriggerAPIView.as_view(),
        name="project-restore",
    ),
    path(
        "projects/<int:project_id>/cool",
        api_views.ProjectCoolTriggerAPIView.as_view(),
        name="project-cool",
    ),
    path(
        "projects/<slug:project_slug>/lifecycle",
        api_views.ProjectLifecycleAPIView.as_view(),
        name="project-lifecycle",
    ),
    path(
        "operations/callback",
        api_views.LifecycleOperationCallbackAPIView.as_view(),
        name="operations-callback",
    ),
)
