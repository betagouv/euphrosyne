import os

from euphrosyne import settings


def test_default_mailer_uses_smtp_options():
    default_mailer = settings.MAILERS["default"]

    assert default_mailer["BACKEND"] == "django.core.mail.backends.smtp.EmailBackend"
    assert default_mailer["OPTIONS"] == {
        "host": os.environ["EMAIL_HOST"],
        "port": int(os.environ["EMAIL_PORT"]),
        "username": os.environ["EMAIL_HOST_USER"],
        "password": os.environ["EMAIL_HOST_PASSWORD"],
        "use_tls": os.getenv("EMAIL_USE_TLS") != "false",
    }
