from django.urls import path

from .api_views.calendar import CalendarView
from .api_views.project import ProjectList
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
        "runs/<int:pk>/methods",
        RunMethodsView.as_view(),
        name="run-detail-methods",
    ),
]
