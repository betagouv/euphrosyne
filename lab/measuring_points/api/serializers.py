from rest_framework import serializers

from ..models import MeasuringPoint


class MeasuringPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasuringPoint
        fields = (
            "id",
            "name",
            "run",
            "object_group",
            "comments",
        )
        read_only_fields = ("run",)
