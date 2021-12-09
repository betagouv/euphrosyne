from typing import List

from django.contrib import admin
from django.urls import path
from django.urls.resolvers import URLResolver

from lab.views import ChangeLeaderView, ProjectDocumentsUploadView, ProjectDocumentsView


class AdminSite(admin.AdminSite):
    login_template = "euphro_admin/login.html"

    site_title = "Euphrosyne"
    site_header = "Euphrosyne"
    index_title = ""

    def get_urls(self) -> List[URLResolver]:
        return [
            path(
                "admin/lab/project/<project_id>/leader/change",
                self.admin_view(ChangeLeaderView.as_view()),
                name="lab_project_leader_participation_change",
            ),
            path(
                "admin/lab/project/<project_id>/documents",
                self.admin_view(ProjectDocumentsView.as_view()),
                name="lab_project_documents",
            ),
            path(
                "admin/lab/project/<project_id>/documents/upload",
                self.admin_view(ProjectDocumentsUploadView.as_view()),
                name="lab_project_documents_upload",
            ),
            *super().get_urls(),
        ]
