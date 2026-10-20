import json
from html.parser import HTMLParser
from types import SimpleNamespace

import pytest
from django.template import Context, engines
from django.template.loader_tags import BlockNode
from django.test import TestCase
from django.urls import reverse

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from lab.tests.factories import ProjectWithLeaderFactory, RunFactory

PAYLOAD = '</script><script>alert("XSS")</script><img src=x onerror=alert(1)>'
SPECIAL_CHARACTERS = 'Élodie "quoted" \\ newline\n& < > \u2028\u2029'


class ScriptParser(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.scripts: dict[str, list[str]] = {}
        self.current_id: str | None = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/json":
            self.current_id = dict(attrs).get("id")
            if self.current_id:
                assert self.current_id not in self.scripts
                self.scripts[self.current_id] = []

    def handle_endtag(self, tag):
        if tag == "script":
            self.current_id = None

    def handle_data(self, data):
        if self.current_id:
            self.scripts[self.current_id].append(data)

    def data(self, element_id: str):
        content = "".join(self.scripts[element_id])
        assert "<" not in content
        assert ">" not in content
        assert "&" not in content
        return json.loads(content)


class TestScriptJsonData(TestCase):
    def test_authenticated_view_has_script_data(self):
        user = StaffUserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse("admin:lab_project_changelist"))

        assert response.status_code == 200
        scripts = ScriptParser(response.content.decode())
        assert scripts.data("top-header-data") == {"project": None, "backLink": None}
        assert scripts.data("nav-items-data")["currentPath"] == "/lab/project/"
        assert scripts.data("user-data") == {
            "fullName": user.get_full_name(),
            "isLabAdmin": False,
            "id": user.id,
            "accountURL": reverse("admin:euphro_auth_user_change", args=[user.id]),
            "email": user.email,
        }
        assert scripts.data("feature-flags")

    def test_project_add_has_default_header(self):
        self.client.force_login(StaffUserFactory())
        response = self.client.get(reverse("admin:lab_project_add"))
        assert response.status_code == 200
        scripts = ScriptParser(response.content.decode())
        assert scripts.data("top-header-data") == {"project": None, "backLink": None}
        assert scripts.data("project-changeform-data")["projectId"] is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_name",
    [
        "admin:lab_project_change",
        "admin:lab_run_changelist",
        "admin:lab_run_change",
        "admin:lab_project_documents",
        "admin:lab_project_workplace",
        "admin:lab_project_hdf5_viewer",
        "admin:lab_run_notebook",
    ],
)
def test_project_views_escape_script_data(client, view_name):
    project = ProjectWithLeaderFactory()
    leader = project.leader.user
    type(leader).objects.filter(pk=leader.pk).update(first_name=PAYLOAD, last_name="")
    leader.refresh_from_db()
    # Exercise legacy/imported data that bypasses form validators as well.
    type(project).objects.filter(pk=project.pk).update(name=PAYLOAD)
    project.refresh_from_db()
    run = RunFactory(project=project, label=PAYLOAD)
    viewer = LabAdminUserFactory()
    client.force_login(viewer)
    if view_name == "admin:lab_run_changelist":
        url = reverse(view_name) + f"?project={project.id}"
    else:
        object_id = (
            run.id
            if view_name in {"admin:lab_run_change", "admin:lab_run_notebook"}
            else project.id
        )
        url = reverse(view_name, args=[object_id])

    response = client.get(url)

    assert response.status_code == 200
    html = response.content.decode()
    assert PAYLOAD not in html
    scripts = ScriptParser(html)
    header = scripts.data("top-header-data")["project"]
    assert header["name"] == project.name
    assert header["leader"] == leader.get_full_name()
    if view_name == "admin:lab_project_documents":
        assert scripts.data("project-documents-data")["project"]["name"] == project.name
    elif view_name == "admin:lab_project_workplace":
        data = scripts.data("workplace-data")
        assert data["project"]["name"] == project.name
        assert data["runs"][0]["label"] == run.label
    elif view_name == "admin:lab_run_notebook":
        assert scripts.data("notebook-data")["runName"] == run.label
    elif view_name == "admin:lab_run_change":
        assert scripts.data("run-change-form-data")["run"] == {
            "id": str(run.id),
            "label": run.label,
        }


@pytest.mark.django_db
@pytest.mark.parametrize("name", [PAYLOAD, SPECIAL_CHARACTERS])
def test_user_and_navigation_data_round_trip(client, settings, name):
    user = StaffUserFactory()
    type(user).objects.filter(pk=user.pk).update(first_name=name, last_name="")
    user.refresh_from_db()
    settings.NAV_GET_NAV_ITEMS = lambda request: [{"title": name}]
    client.force_login(user)

    response = client.get(reverse("admin:lab_project_changelist"))

    assert response.status_code == 200
    html = response.content.decode()
    assert PAYLOAD not in html
    scripts = ScriptParser(html)
    assert scripts.data("user-data")["fullName"] == user.get_full_name()
    assert scripts.data("nav-items-data")["items"][0]["title"] == name


@pytest.mark.parametrize("label", [PAYLOAD, SPECIAL_CHARACTERS])
def test_objectgroup_header_escapes_run_label(label):
    blocks = (
        engines["django"]
        .engine.get_template("admin/lab/objectgroup/change_form.html")
        .nodelist.get_nodes_by_type(BlockNode)
    )
    block = next(block for block in blocks if block.name == "top_header_data")
    html = block.render(
        Context({"objectgroup_run": SimpleNamespace(id=1, label=label)})
    )
    assert ScriptParser(html).data("top-header-data")["backLink"] == {
        "href": reverse("admin:lab_run_change", args=[1]),
        "title": label,
    }
