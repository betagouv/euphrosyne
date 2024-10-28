import datetime

from django.utils import timezone
from rest_framework import reverse, serializers

from ..models import Project, Run
from ..objects.models import ObjectGroup, RunObjetGroupImage


class ProjectRunObjectGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectGroup
        fields = ("label", "id")


class ProjectRunSerializer(serializers.ModelSerializer):
    objects = ProjectRunObjectGroupSerializer(many=True, source="run_object_groups")
    methods_url = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = (
            "label",
            "particle_type",
            "energy_in_keV",
            "objects",
            "methods_url",
        )

    def get_methods_url(self, obj: Run):
        return reverse.reverse(
            "api:run-detail-methods", args=[obj.id], request=self.context["request"]
        )


class ProjectSerializer(serializers.ModelSerializer):
    runs = ProjectRunSerializer(many=True)

    class Meta:
        model = Project
        fields = ("name", "runs", "slug")


class UpcomingProjectSerializer(serializers.ModelSerializer):
    change_url = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    num_runs = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ("name", "start_date", "change_url", "status", "num_runs")

    def get_change_url(self, obj: Project):
        return reverse.reverse("admin:lab_project_change", args=[obj.id])

    def get_start_date(self, obj: Project):
        # Get start_date by ordering runs by start_date and filtering the
        # ones that are after now
        ordered_start_dates = [
            r.start_date
            for r in sorted(
                filter(
                    lambda r: r.start_date and r.start_date >= timezone.now(),
                    obj.runs.all(),
                ),
                key=lambda r: r.start_date or datetime.datetime.max,
            )
        ]
        if not ordered_start_dates:
            return None
        return ordered_start_dates[0]

    def get_num_runs(self, obj: Project):
        return obj.runs.count()

    def get_status(self, obj: Project):
        return {
            "label": obj.status.value[1],
            "class_name": obj.status.name.lower(),
        }


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


class _RunObjectGroupObjectGroupSerializer(serializers.ModelSerializer):
    dating = serializers.SerializerMethodField()

    class Meta:
        model = ObjectGroup
        fields = ("label", "id", "object_count", "dating", "materials", "c2rmf_id")

    def get_dating(self, obj: ObjectGroup):
        return obj.dating_era.label if obj.dating_era else ""


class RunObjectGroupSerializer(serializers.ModelSerializer):
    objectgroup = _RunObjectGroupObjectGroupSerializer()

    class Meta:
        model = Run.run_object_groups.through
        fields = ("id", "objectgroup")


class AvailableObjectGroupSerializer(_RunObjectGroupObjectGroupSerializer):
    pass


class RunObjectGroupCreateSerializer(serializers.ModelSerializer):
    objectgroup = serializers.PrimaryKeyRelatedField(queryset=ObjectGroup.objects.all())

    class Meta:
        model = Run.run_object_groups.through
        fields = ("objectgroup",)


class ObjectGroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectGroup
        fields = (
            "id",
            "label",
        )
        read_only_fields = ("id",)


class RunObjectGroupImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunObjetGroupImage
        fields = ("id", "path", "transform")

        read_only_fields = ("id",)
