import json

import pytest
from django.test import RequestFactory
from django.urls import get_resolver, reverse
from django.utils.translation import gettext_lazy as _

from lab.templatetags.projects import project_header_json_data, project_tabs
from lab.tests.factories import ProjectWithLeaderFactory

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


@pytest.mark.django_db
def test_project_header_json_data():
    project = ProjectWithLeaderFactory()
    data = json.loads(project_header_json_data(project.id))

    assert "project" in data
    assert "backLink" in data

    project_data = data["project"]
    assert project_data["name"] == project.name
    assert project_data["leader"] == project.leader.user.get_full_name()
    status_data = project_data["status"]
    assert status_data["label"] == str(project.status.value[1])
    assert status_data["className"] == project.status.name.lower()

    assert data["backLink"]["href"] == reverse("admin:lab_project_changelist")
    assert data["backLink"]["title"] == str(_("Project"))
