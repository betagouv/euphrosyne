from collections import OrderedDict
from unittest import mock

from django.test import SimpleTestCase, TestCase

from ...api_views.serializers import (
    ProjectRunSerializer,
    ProjectSerializer,
    RunMethodsSerializer,
)
from ...models import Run
from .. import factories


class TestProjectSerializer(TestCase):
    @mock.patch.object(
        ProjectRunSerializer, "get_methods_url", mock.MagicMock(return_value="URL")
    )
    def test_project_serializers(self):
        run = factories.RunFactory()
        objectgroup = factories.ObjectGroupFactory()
        run.run_object_groups.add(objectgroup)

        serializer = ProjectSerializer(run.project)
        serializer.context["request"] = mock.MagicMock()

        assert serializer.data == {
            "name": run.project.name,
            "runs": [
                OrderedDict(
                    [
                        ("label", run.label),
                        ("particle_type", str(run.particle_type)),
                        ("energy_in_keV", run.energy_in_keV),
                        (
                            "objects",
                            [
                                OrderedDict(
                                    [
                                        ("label", objectgroup.label),
                                        ("id", objectgroup.id),
                                    ]
                                )
                            ],
                        ),
                        ("methods_url", "URL"),
                    ]
                )
            ],
            "slug": run.project.slug,
        }

    def test_run_serializer_get_methods_url(self):
        with mock.patch("lab.api_views.serializers.reverse.reverse") as mock_fn:
            run = Run(id=1, label="run")
            request_mock = mock.MagicMock()

            serializer = ProjectRunSerializer(run)
            serializer.context["request"] = request_mock

            serializer.get_methods_url(run)

            mock_fn.assert_called_with(
                "api:run-detail-methods", args=[run.id], request=request_mock
            )


class TestRunMethodsSerializer(SimpleTestCase):
    def test_serializer(self):
        run = factories.RunFactory.build()

        serializer = RunMethodsSerializer(instance=run)
        assert serializer.data == {
            "method_PIXE": False,
            "method_PIGE": False,
            "method_IBIL": False,
            "method_FORS": False,
            "method_RBS": False,
            "method_ERDA": False,
            "method_NRA": False,
            "detector_LE0": False,
            "detector_HE1": False,
            "detector_HE2": False,
            "detector_HE3": False,
            "detector_HE4": False,
            "detector_HPGe20": False,
            "detector_HPGe70": False,
            "detector_HPGe70N": False,
            "detector_IBIL_QE65000": False,
            "detector_IBIL_other": "",
            "detector_FORS_QE65000": False,
            "detector_FORS_other": "",
            "detector_PIPS130": False,
            "detector_PIPS150": False,
            "detector_ERDA": "",
            "detector_NRA": "",
            "filters_for_detector_LE0": "",
            "filters_for_detector_HE1": "",
            "filters_for_detector_HE2": "",
            "filters_for_detector_HE3": "",
            "filters_for_detector_HE4": "",
        }
