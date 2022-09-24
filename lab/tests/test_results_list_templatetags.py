from unittest.mock import patch

from ..models.project import Project
from ..templatetags.list_results import project_results


@patch.object(Project, "status", new=Project.Status.TO_SCHEDULE)  # prevent DB call
def test_custom_result_list():
    project = Project(pk=1)

    assert project_results(0, [project], [["old status repr"]]) == [
        [
            '<td class="field-status"><span class="fr-tag fr-tag--sm to_schedule">'
            + project.status.value[1]
            + "</span></td>"
        ]
    ]
