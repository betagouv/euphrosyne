from django.conf import settings
from social_core.backends.orcid import ORCIDOAuth2 as SocialORCIDOAuth2


class ORCIDOAuth2(SocialORCIDOAuth2):  # pylint: disable=abstract-method
    BASE_DOMAIN = "sandbox.orcid.org" if settings.ORCID_USE_SANDBOX else "orcid.org"

    AUTHORIZATION_URL = f"https://{BASE_DOMAIN}/oauth/authorize"
    ACCESS_TOKEN_URL = f"https://{BASE_DOMAIN}/oauth/token"
    USER_ID_URL = f"https://{BASE_DOMAIN}/oauth/userinfo"
    USER_DATA_URL = f"https://pub.{BASE_DOMAIN}/v2.0/" + "{}"

    def get_key_and_secret(self):
        return (
            getattr(settings, "SOCIAL_AUTH_ORCID_KEY"),
            getattr(settings, "SOCIAL_AUTH_ORCID_SECRET"),
        )
