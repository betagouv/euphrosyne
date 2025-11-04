from django.urls import path

from . import api_views

urlpatterns = (
    path(
        "user/<int:user_id>",
        api_views.UserRadiationProtectionResultRetrieveView.as_view(),
        name="retrieve_user_radiation_protection_result",
    ),
)
