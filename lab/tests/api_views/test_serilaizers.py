from lab.api_views.serializers import ProjectSerializer


def test_project_serializers():
    assert ProjectSerializer.Meta.fields == (
        "id",
        "name",
    )
