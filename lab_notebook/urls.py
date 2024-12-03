from django.contrib.admin import site
from django.urls import path

from . import views
from .pdf_export.views import export_notebook_to_pdf_view

urlpatterns = [
    path(
        "lab/run/<run_id>/notebook",
        site.admin_view(views.NotebookView.as_view()),  # type: ignore[type-var]
        name="lab_run_notebook",
    ),
    path(
        "lab/run/<run_id>/notebook/export-pdf",
        site.admin_view(export_notebook_to_pdf_view),  # type: ignore[type-var]
        name="lab_run_notebook_export_pdf",
    ),
]
