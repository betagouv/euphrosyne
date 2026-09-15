import re

import pytest
from django.test import Client
from django.urls import URLPattern, reverse
from django.utils.html import escape

from ..urls import urlpatterns


@pytest.mark.parametrize("url", urlpatterns)
def test_static_page_access_when_anonymous(url: URLPattern):
    """Test access to page when not logged in.
    Should not redirect to login page."""
    response = Client().get(reverse(url.name))
    assert response.status_code == 200
    assert b'<header role="banner" class="fr-header">' in response.content
    assert f'href="{reverse("admin:index")}"'.encode() in response.content
    assert f'href="{reverse("admin:login")}"'.encode() in response.content


@pytest.mark.parametrize(
    ("language", "title", "expected_text", "unexpected_text"),
    [
        (
            "fr",
            "Déclaration d'accessibilité",
            "État de conformité",
            "Compliance status",
        ),
        (
            "en",
            "Accessibility declaration",
            "Compliance status",
            "État de conformité",
        ),
    ],
)
def test_accessibility_declaration_is_localized(
    language: str, title: str, expected_text: str, unexpected_text: str
):
    response = Client().get(
        reverse("static_accessibility_declaration"),
        headers={"accept-language": language},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert re.search(rf'<div class="fr-container">\s*<h1>{escape(title)}</h1>', content)
    assert expected_text in content
    assert unexpected_text not in content
