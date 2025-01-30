from django.urls import path

from . import api_views

urlpatterns = [
    path(
        "",
        api_views.feedback_view,
        name="create",
    )
]
