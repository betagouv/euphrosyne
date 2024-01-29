from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from lab.tests.factories import ProjectWithLeaderFactory, StaffUserFactory


class TestScriptJsonData(TestCase):
    def test_authenticated_view_has_script_data(self):
        url = reverse("admin:lab_project_changelist")
        user = StaffUserFactory()
        request = RequestFactory().get(url)
        request.user = user
        self.client.force_login(user)

        response = self.client.get(url)

        html = response.content.decode("utf-8")
        assert 'script id="top-header-data" type="application/json"' in html
        assert '{"project": null, "backLink": null}' in html

        assert '<script id="nav-items-data" type="application/json">' in html
        # pylint: disable=line-too-long
        assert (
            '{"currentPath": "/lab/project/", "items": [{"title": "Projets", "href": "/lab/project/", "iconName": "fr-icon-survey-line", "extraPath": ["/lab/run/"], "exactPath": false}]}'
            in html
        )

        assert '<script id="user-data" type="application/json">' in html
        assert (
            f""""fullName": "{user.get_full_name()}",\n      "isLabAdmin": false\n"""
            in html
        )

    def test_project_header_data(self):
        project = ProjectWithLeaderFactory()
        url = reverse("admin:lab_project_change", args=(project.id,))
        request = RequestFactory().get(url)
        request.user = project.leader.user
        self.client.force_login(project.leader.user)

        response = self.client.get(url)

        html = response.content.decode("utf-8")
        print(html)
        assert 'script id="top-header-data" type="application/json"' in html
        # pylint: disable=line-too-long
        top_header_data = (
            '{"backLink": {"href": "/lab/project/", "title": "%s"}, "project": {"name": "%s", "leader": "%s", "status": {"label": "%s", "className": "to_schedule"}}}'
            % (
                _("Project"),
                project.name,
                project.leader.user.get_full_name(),
                project.status.value[1],
            )
        )
        assert top_header_data in html
