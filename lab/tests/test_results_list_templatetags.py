from ..models.project import Project
from ..templatetags.list_results import project_results


def test_custom_result_list():
    project = Project(status=Project.Status.ONGOING)

    assert project_results(0, [project], [["old status repr"]]) == [
        [
            '<td class="field-status"><span class="fr-tag fr-tag--sm ongoing">'
            "A planifier"
            "</span></td>"
        ]
    ]
