import pytest
from django.test import RequestFactory
from django.urls import get_resolver, reverse

from lab.templatetags.projects import project_tabs

URLS_MAPPING = {
    reverse("admin:lab_project_change", args=[1]): 0,
    reverse("admin:lab_run_changelist"): 1,
    reverse("admin:lab_run_change", args=[1]): 1,
    reverse("admin:lab_run_add"): 1,
    reverse("admin:lab_project_documents", args=[1]): 2,
}


def test_project_tags_return_value():
    request = RequestFactory().get(reverse("admin:lab_project_change", args=[1]))
    resolver = get_resolver()
    request.resolver_match = resolver.resolve(request.path_info)
    tabs = project_tabs(1, request)
    assert "tabs" in tabs
    assert all("name" in tab for tab in tabs["tabs"])
    assert all("url" in tab for tab in tabs["tabs"])
    assert all("is_active" in tab for tab in tabs["tabs"])


@pytest.mark.parametrize("url", URLS_MAPPING.keys())
def test_project_tags_is_active_value(url):
    request = RequestFactory().get(url)
    resolver = get_resolver()
    request.resolver_match = resolver.resolve(request.path_info)
    tabs = project_tabs(1, request)
    assert tabs["tabs"][URLS_MAPPING[url]]["is_active"]
