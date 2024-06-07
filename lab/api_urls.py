from django.urls import include, path

from .api_views.calendar import CalendarView
from .api_views.objectgroup import get_eros_object
from .api_views.project import ProjectList, UpcomingProjectList
from .api_views.run import RunMethodsView
from .api_views.run_objectgroup import (
    RunObjectGroupAvailableListView,
    RunObjectGroupDeleteView,
    RunObjectGroupView,
)

urlpatterns = [
    path(
        "calendar/",
        CalendarView.as_view(),
        name="calendar",
    ),
    path(
        "projects/",
        ProjectList.as_view(),
        name="project-list",
    ),
    path(
        "projects/upcoming",
        UpcomingProjectList.as_view(),
        name="project-upcoming-list",
    ),
    path(
        "runs/<int:run_id>/objectgroups",
        RunObjectGroupView.as_view(),
        name="run-objectgroup-list",
    ),
    path(
        "runs/<int:run_id>/available-objectgroups",
        RunObjectGroupAvailableListView.as_view(),
        name="run-objectgroup-list",
    ),
    path(
        "run_objectgroups/<int:pk>",
        RunObjectGroupDeleteView.as_view(),
        name="run-objectgroup-list",
    ),
    path(
        "runs/<int:pk>/methods",
        RunMethodsView.as_view(),
        name="run-detail-methods",
    ),
    path(
        "objectgroup/c2rmf-fetch",
        get_eros_object,
        name="objectgroup-c2rmf-fetch",
    ),
    path("catalog/", include("lab.elasticsearch.api_urls"), name="catalog-api"),
]
