from django.urls import path

from .views import (
    MeasuringPointStandardView,
    RunMeasuringPointStandardView,
    StandardListView,
)

urlpatterns = [
    path(
        "standards",
        StandardListView.as_view(),
        name="standard_list",
    ),
    path(
        "runs/<int:run_id>",
        RunMeasuringPointStandardView.as_view(),
        name="run_standard_list",
    ),
    path(
        "measuring-points/<int:measuring_point_id>/standard",
        MeasuringPointStandardView.as_view(),
        name="measuring_point_standard",
    ),
]
