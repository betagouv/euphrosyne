from django.urls import path

from .run import views as run_views

urlpatterns = [
    path(
        "run-notebook/<run_id>",
        run_views.RunNotebookView.as_view(),
        name="run_notebook_change",
    ),
]
