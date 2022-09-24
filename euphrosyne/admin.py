from typing import List

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from django.urls.resolvers import URLResolver

from lab.documents.views import ProjectDocumentsView
from lab.views import ChangeLeaderView
from lab.workplace.views import WorkplaceView


class AdminSite(admin.AdminSite):
    login_template = "euphro_admin/login.html"
    password_change_template = "euphro_admin/password_reset_form.html"

    site_title = "Euphrosyne"
    site_header = "Euphrosyne"
    index_title = ""

    def get_urls(self) -> List[URLResolver]:
        return [
            path(
                "lab/project/<project_id>/leader/change",
                self.admin_view(ChangeLeaderView.as_view()),
                name="lab_project_leader_participation_change",
            ),
            path(
                "lab/project/<project_id>/documents",
                self.admin_view(ProjectDocumentsView.as_view()),
                name="lab_project_documents",
            ),
            path(
                "lab/project/<project_id>/workplace",
                self.admin_view(WorkplaceView.as_view()),
                name="lab_project_workplace",
            ),
            *super().get_urls(),
        ]

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        for app in app_list:
            for model_dict in app["models"]:
                model_admin = self._registry[model_dict["model"]]
                if getattr(model_admin, "HIDE_ADD_SIDEBAR", None):
                    model_dict["add_url"] = None
        return app_list

    def index(self, request, extra_context=None):
        if not request.user.is_lab_admin and request.path == "/":
            return redirect(reverse("admin:lab_project_changelist"))
        return super().index(request, extra_context=extra_context)
