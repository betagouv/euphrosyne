from django.contrib.admin import site
from django.urls import path

from . import views

urlpatterns = [
    path(
        "lab/run/<run_id>/notebook",
        site.admin_view(views.NotebookView.as_view()),  # type: ignore[type-var]
        name="lab_run_notebook",
    ),
]
