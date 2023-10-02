from django.urls import path

from . import views

urlpatterns = [
    path("cgu/", views.cgu_view, name="static_cgu"),
    path("legal-notice/", views.legal_notice_view, name="static_legal_notice"),
    path("personal-data/", views.personal_data_view, name="static_personal_data"),
    path(
        "accessibility/declaration/",
        views.accessibility_declaration_view,
        name="static_accessibility_declaration",
    ),
    path(
        "accessibility/multiyear-schema/",
        views.accessibility_multiyear_schema_view,
        name="static_accessibility_multiyear_schema",
    ),
    path(
        "accessibility/site-map/",
        views.accessibility_map_view,
        name="static_accessibility_site_map",
    ),
]
