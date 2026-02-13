from django.apps import apps
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

app_name = "api"

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs", SpectacularSwaggerView.as_view(url_name="api:schema"), name="docs"),
    path("auth/", include("euphro_auth.api_urls")),
    path("lab/", include("lab.api_urls")),
    path("standard/", include("standard.api.urls")),
    path("feedback/", include("feedback.api_urls"), name="feedback"),
]

if apps.is_installed("data_request"):
    urlpatterns.append(path("data-request/", include("data_request.api_urls")))

if apps.is_installed("data_management"):
    urlpatterns.append(path("data-management/", include("data_management.api_urls")))

if apps.is_installed("lab_notebook"):
    urlpatterns.append(path("notebook/", include("lab_notebook.api.urls")))

if apps.is_installed("radiation_protection"):
    urlpatterns.append(
        path(
            "radiation-protection/",
            include("radiation_protection.api_urls"),
            name="radiation_protection",
        )
    )
