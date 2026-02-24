from django.urls import path

from . import api_views

app_name = "data_management"

urlpatterns = (
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
