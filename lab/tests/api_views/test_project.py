from lab.api_views.project import IsLabAdminUser, ProjectList, ProjectSerializer


def test_project_list_conf():
    assert ProjectList.serializer_class == ProjectSerializer
    assert IsLabAdminUser in ProjectList.permission_classes
