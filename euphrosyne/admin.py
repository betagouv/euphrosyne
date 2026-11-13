from allauth.account.views import login as account_login
from allauth.account.views import logout as account_logout
from django.apps import apps
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path, reverse
from django.urls.resolvers import URLPattern, URLResolver
from django.utils.translation import gettext_lazy as _

from lab.documents.views import ProjectDocumentsView
from lab.hdf5.views import HDF5View
from lab.objects.views import ObjectImportErosView, ObjectImportPOPView
from lab.workplace.views import WorkplaceView


class AdminSite(admin.AdminSite):
    site_title = "Euphrosyne"
    site_header = "Euphrosyne"
    index_title = _("Dashboard")

    # Sign-in, sign-out and password change are handled by django-allauth.
    def login(self, request, extra_context=None):
        return account_login(request)

    def logout(self, request, extra_context=None):
        return account_logout(request)

    def password_change(self, request, extra_context=None):
        return redirect("account_change_password")

    def get_urls(self) -> list[URLPattern | URLResolver]:  # type: ignore[override]
        urls: list[URLPattern | URLResolver] = [
            path(
                "lab/project/<project_id>/documents",
                self.admin_view(ProjectDocumentsView.as_view()),  # type: ignore[type-var] # pylint: disable=line-too-long
                name="lab_project_documents",
            ),
            path(
                "lab/project/<project_id>/workplace",
                self.admin_view(WorkplaceView.as_view()),  # type: ignore[type-var]
                name="lab_project_workplace",
            ),
            path(
                "lab/objectgroup/eros_import",
                self.admin_view(ObjectImportErosView.as_view()),  # type: ignore[type-var] # pylint: disable=line-too-long
                name="lab_objectgroup_erosimport",
            ),
            path(
                "lab/objectgroup/pop_import",
                self.admin_view(ObjectImportPOPView.as_view()),  # type: ignore[type-var] # pylint: disable=line-too-long
                name="lab_objectgroup_popimport",
            ),
        ]

        if apps.is_installed("lab_notebook"):
            urls.append(path("", include("lab_notebook.urls")))

        urls.append(
            path(
                "lab/project/<project_id>/hdf5-viewer",
                self.admin_view(HDF5View.as_view()),  # type: ignore[type-var]
                name="lab_project_hdf5_viewer",
            )
        )
        return [*urls, *super().get_urls()]  # type: ignore[list-item]

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


def allauth_models_without_admin() -> list:
    """allauth admin pages the platform does not offer:

    - authenticators hold TOTP secrets: superusers reset them from the users;
    - email addresses would sign in: User.email is the only address;
    - the ORCID app is configured in settings, a second one breaks sign-in;
    - OAuth tokens are not stored."""
    # pylint: disable=import-outside-toplevel
    from allauth.account.models import EmailAddress
    from allauth.mfa.models import Authenticator
    from allauth.socialaccount.models import SocialApp, SocialToken

    return [Authenticator, EmailAddress, SocialApp, SocialToken]
