import pytest
from django.test import Client
from django.urls import URLPattern, reverse

from ..urls import urlpatterns


@pytest.mark.parametrize("url", urlpatterns)
def test_static_page_access_when_anonymous(url: URLPattern):
    """Test access to page when not logged in.
    Should not redirect to login page."""
    response = Client().get(reverse(url.name))
    assert response.status_code == 200
