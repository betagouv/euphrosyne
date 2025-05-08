from django.urls import path

from . import api_views

urlpatterns = (
    path("list-all", api_views.list_all_items, name="list-all"),
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
