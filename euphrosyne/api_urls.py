from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("", include("lab.documents.api_urls")),
    path("", include("lab.workplace.api_urls")),
]
