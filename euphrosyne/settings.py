"""
Django settings for euphrosyne project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import subprocess

# pylint: disable=line-too-long
from datetime import datetime
from pathlib import Path

import dj_database_url
import psycopg2
import sentry_sdk
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from sentry_sdk.integrations.django import DjangoIntegration

# pylint: disable=abstract-class-instantiated
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment=os.getenv("SENTRY_ENVIRONMENT"),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.getenv("DJANGO_DEBUG", ""))

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split() or (
    ["localhost", ".scalingo.io"] if not DEBUG else []
)

CORS_ALLOWED_ORIGINS = (
    os.environ["CORS_ALLOWED_ORIGINS"].split(",")
    if os.getenv("CORS_ALLOWED_ORIGINS")
    else []
)

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split()

SITE_URL = os.environ["SITE_URL"]


# Application definition

INSTALLED_APPS = [
    "corsheaders",
    "euphrosyne.apps.AdminConfig",
    "euphrosyne.methods.apps.MethodsConfig",  # Use explicit app config for methods
    "euphro_auth",
    "django.forms",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
    "rest_framework",
    "django_filters",
    "lab",
    "data_request",
    "lab_notebook",
    "orcid_oauth",
    "static_pages",
    "standard",
    "drf_spectacular",
] + (["debug_toolbar"] if DEBUG else [])

MIDDLEWARE = (["debug_toolbar.middleware.DebugToolbarMiddleware"] if DEBUG else []) + [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "euphro_auth.middleware.UserLanguageMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "euphro_auth.middlewares.CGUAcceptanceMiddleware",
]

ROOT_URLCONF = "euphrosyne.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "euphrosyne/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

WSGI_APPLICATION = "euphrosyne.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {}


def build_development_db_name(base_db_name):
    branch_suffix = (
        subprocess.check_output(
            [
                (
                    Path(BASE_DIR) / Path("scripts") / Path("db_suffix_for_branch.sh")
                ).resolve()
            ]
        )
        .strip()
        .decode("utf-8")
    )
    branch_db_name = f"{base_db_name}_{branch_suffix}"

    # pylint: disable=no-else-return
    try:
        conn = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=branch_db_name,
        )
    except psycopg2.OperationalError:
        print(f"🅸 Using normal database {base_db_name}")
        return base_db_name
    else:
        conn.close()
        print(f"🆈 Using branch database {branch_db_name}")
        return branch_db_name


_djdb_config = dj_database_url.config()
if _djdb_config:
    DATABASES["default"] = _djdb_config
elif os.getenv("DB_HOST"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "USER": os.getenv("DB_USER", ""),
        "NAME": build_development_db_name(os.getenv("DB_NAME")),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": 60,
    }
else:  # Use sqlite by default, for ci
    print("⚠️  No postgres database, running on SQLite")
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase",
    }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Authentication backends
# https://docs.djangoproject.com/en/dev/topics/auth/customizing/#other-authentication-sources

AUTHENTICATION_BACKENDS = [
    "orcid_oauth.backends.ORCIDOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
]

LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = ["locale"]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "objectstorage": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "azure_container": "static",
            "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
            "overwrite_files": True,
        },
    },
}


STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "_static")

STATICFILES_DIRS = [
    BASE_DIR / "euphrosyne/assets/dist",
    BASE_DIR / "euphrosyne/static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model

AUTH_USER_MODEL = "euphro_auth.User"

# For Python Social Auth; used for ORCID OAuth 2.0 flow

ORCID_USE_SANDBOX = os.getenv("ORCID_USE_SANDBOX", "false") == "true"

SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ["user_id"]
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/"
SOCIAL_AUTH_ORCID_KEY = os.getenv("SOCIAL_AUTH_ORCID_KEY")
SOCIAL_AUTH_ORCID_SECRET = os.getenv("SOCIAL_AUTH_ORCID_SECRET")
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "orcid_oauth.pipeline.social_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "orcid_oauth.pipeline.complete_information",
)
SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_USER_MODEL = "euphro_auth.User"


# For Django Debug Toolbar

INTERNAL_IPS = ["127.0.0.1"]

# Sending emails
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = os.environ["EMAIL_PORT"]

EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") != "false"

DEFAULT_FROM_EMAIL = os.environ["DEFAULT_FROM_EMAIL"]

FEEDBACK_EMAILS = os.getenv("FEEDBACK_EMAILS", "").split(",")

# Necessary for the correct behavior of password reset flow:
LOGIN_URL = "/login/"

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "propagate": True,
        },
        "": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
}

EUPHROSYNE_TOOLS_API_URL = os.environ["EUPHROSYNE_TOOLS_API_URL"]
EROS_BASE_IMAGE_URL = os.getenv("EROS_BASE_IMAGE_URL")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_BUCKET_REGION_NAME = os.getenv("S3_BUCKET_REGION_NAME")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


HDF5_ENABLE = os.getenv("HDF5_ENABLE", "false") == "true"

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")
ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")


def _get_nav_items(request: HttpRequest) -> list:
    from .nav import get_nav_items  # pylint: disable=import-outside-toplevel

    return get_nav_items(request)


NAV_GET_NAV_ITEMS = _get_nav_items


FORCE_LAST_CGU_ACCEPTANCE_DT = (
    timezone.make_aware(
        datetime.fromisoformat(os.environ["FORCE_LAST_CGU_ACCEPTANCE_DT"])
    )
    if os.getenv("FORCE_LAST_CGU_ACCEPTANCE_DT")
    else None
)
# Lab-specific method model configuration
# This should point to the concrete implementation with field definitions
# All migrations related to these fields will be generated in the euphrosyne app
METHOD_MODEL_CLASS = "euphrosyne.methods.models.EuphrosyneMethodModel"
