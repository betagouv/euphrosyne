from rest_framework import serializers

from ..models import Project, Run
from ..objects.models import ObjectGroup


class ProjectRunObjectGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectGroup
        fields = ("label", "id")


class ProjectRunSerializer(serializers.ModelSerializer):
    objects = ProjectRunObjectGroupSerializer(many=True, source="run_object_groups")

    class Meta:
        model = Run
        fields = ("id", "label", "particle_type", "energy_in_keV", "objects")


class ProjectSerializer(serializers.ModelSerializer):
    runs = ProjectRunSerializer(many=True)

    class Meta:
        model = Project
        fields = ("name", "runs", "slug")


class RunMethodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = (
            "method_PIXE",
            "method_PIGE",
            "method_IBIL",
            "method_FORS",
            "method_RBS",
            "method_ERDA",
            "method_NRA",
            "detector_LE0",
            "detector_HE1",
            "detector_HE2",
            "detector_HE3",
            "detector_HE4",
            "detector_HPGe20",
            "detector_HPGe70",
            "detector_HPGe70N",
            "detector_IBIL_QE65000",
            "detector_IBIL_other",
            "detector_FORS_QE65000",
            "detector_FORS_other",
            "detector_PIPS130",
            "detector_PIPS150",
            "detector_ERDA",
            "detector_NRA",
            "filters_for_detector_LE0",
            "filters_for_detector_HE1",
            "filters_for_detector_HE2",
            "filters_for_detector_HE3",
            "filters_for_detector_HE4",
        )
