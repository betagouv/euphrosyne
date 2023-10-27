"""euphrosyne URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import JavaScriptCatalog
from graphene_django.views import GraphQLView

from euphro_auth.views import UserTokenRegistrationView
from orcid_oauth.views import UserCompleteAccountView

urlpatterns = [
    path("", include("social_django.urls")),
    path("doc/", include("django.contrib.admindocs.urls")),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "registration/<uidb64>/<token>/",
        UserTokenRegistrationView.as_view(),
        name="registration_token",
    ),
    path(
        "registration/orcid/verify/<token>",
        UserCompleteAccountView.as_view(),
        name="complete_registration_orcid",
    ),
    path("api/", include("euphrosyne.api_urls"), name="api"),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

urlpatterns += [
    path("", include("static_pages.urls")),
    path("", admin.site.urls),
]
