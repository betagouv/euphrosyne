from django.urls import path

from . import views

urlpatterns = [
    path("cgu/", views.cgu_view, name="static_cgu"),
    path("legal-notice/", views.legal_notice_view, name="static_legal_notice"),
    path("personal-data/", views.personal_data_view, name="static_personal_data"),
]
