from django.urls import include, path
from django.views.generic import TemplateView

app_name = "api"

urlpatterns = [
    path(
        "docs",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
    path("auth/", include("euphro_auth.api_urls")),
    path("lab/", include("lab.api_urls")),
    path("data-request/", include("data_request.api_urls")),
    path("notebook/", include("lab_notebook.api.urls")),
]
