from django.apps import apps
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

app_name = "api"

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs", SpectacularSwaggerView.as_view(url_name="api:schema"), name="docs"),
    path("auth/", include("euphro_auth.api_urls")),
    path("lab/", include("lab.api_urls")),
    path("data-request/", include("data_request.api_urls")),
    path("notebook/", include("lab_notebook.api.urls")),
    path("standard/", include("standard.api.urls")),
    path("feedback/", include("feedback.api_urls"), name="feedback"),
]

if apps.is_installed("radiation_protection"):
    urlpatterns.append(
        path(
            "radiation-protection/",
            include("radiation_protection.api_urls"),
            name="radiation_protection",
        )
    )
