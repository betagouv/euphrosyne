from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("auth/", include("euphro_auth.api_urls")),
    path("", include("lab.api_urls")),
]
