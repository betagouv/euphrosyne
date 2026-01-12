from .branding import get_branding


def branding(request):  # pylint: disable=unused-argument
    return get_branding().__dict__
