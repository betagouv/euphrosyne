from django.urls import path

from .api_views.calendar import CalendarView
from .api_views.objects import get_eros_object
from .api_views.project import ProjectList, UpcomingProjectList
from .api_views.run import RunMethodsView

urlpatterns = [
    path(
        "calendar",
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
        "runs/<int:pk>/methods",
        RunMethodsView.as_view(),
        name="run-detail-methods",
    ),
    path(
        "objectgroup/c2rmf-fetch",
        get_eros_object,
        name="objectgroup-c2rmf-fetch",
    ),
]
