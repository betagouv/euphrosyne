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
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from euphro_auth.views import UserTokenRegistrationView, cgu_acceptance_view
from lab.participations.views import complete_employer_information

urlpatterns = [
    path("", include("orcid_oauth.urls")),
    path("doc/", include("django.contrib.admindocs.urls")),
    path("accounts/", include("euphro_auth.urls")),
    path(
        "registration/<uidb64>/<token>/",
        UserTokenRegistrationView.as_view(),
        name="registration_token",
    ),
    path(
        "cgu-acceptance/",
        cgu_acceptance_view,
        name="cgu_acceptance",
    ),
    path(
        "projects/<int:project_id>/employer/",
        complete_employer_information,
        name="participation_employer_completion",
    ),
    path("api/", include("euphrosyne.api_urls"), name="api"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("certification/", include("certification.urls")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

urlpatterns += [
    path("", include("static_pages.urls")),
    path("", admin.site.urls),
]
