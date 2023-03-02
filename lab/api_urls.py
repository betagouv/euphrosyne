from django.urls import path

from .api_views.calendar import CalendarView

urlpatterns = [
    path(
        "calendar",
        CalendarView.as_view(),
        name="calendar",
    ),
]
