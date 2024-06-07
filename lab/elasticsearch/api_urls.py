from django.urls import path

from . import api_views

urlpatterns = (
    path(
        "search",
        api_views.search,
        name="search",
    ),
    path(
        "aggregate",
        api_views.aggregate_field,
        name="aggregate",
    ),
    path(
        "aggregate-created",
        api_views.aggregate_created,
        name="aggregate-created",
    ),
)
