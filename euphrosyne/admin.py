from typing import List

from django.contrib import admin
from django.urls import path
from django.urls.resolvers import URLResolver

from lab.views.change_leader_view import ChangeLeaderView


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
            *super().get_urls(),
        ]
