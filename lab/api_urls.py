from django.urls import path

from .api_views.project import ProjectList

urlpatterns = [
    path(
        "projects/",
        ProjectList.as_view(),
        name="project_list",
    ),
]
