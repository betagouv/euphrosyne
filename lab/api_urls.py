from django.urls import include, path

from .api_views.calendar import CalendarView
from .api_views.objectgroup import ObjectGroupCreateView, get_eros_object
from .api_views.project import ProjectList, UpcomingProjectList
from .api_views.run import RunMethodsView
from .api_views.run_objectgroup import (
    RunObjectGroupAvailableListView,
    RunObjectGroupDeleteView,
    RunObjectGroupImagesView,
    RunObjectGroupView,
)
from .measuring_points.api import views as measuring_points_views

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
        "run_objectgroups/<int:run_object_group_id>/images",
        RunObjectGroupImagesView.as_view(),
        name="run-objectgroup-imagess",
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
    path(
        "objectgroups",
        ObjectGroupCreateView.as_view(),
        name="objectgroups-create",
    ),
    path(
        "runs/<int:run_id>/measuring-points",
        measuring_points_views.MeasuringPointsView.as_view(),
        name="run_measuring_points",
    ),
    path(
        "runs/<int:run_id>/measuring-points/<int:pk>",
        measuring_points_views.MeasuringPointView.as_view(),
        name="run_measuring_point",
    ),
    path(
        "measuring-points/<int:measuring_point_id>/image",
        measuring_points_views.MeasuringPointImageCreateView.as_view(),
        name="run_measuring_point",
    ),
]
