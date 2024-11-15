from rest_framework import serializers

from ...api_views.serializers import RunObjectGroupImageSerializer
from ...objects.models import RunObjetGroupImage
from .. import models


class MeasuringPointImageSerializer(serializers.ModelSerializer):
    run_object_group_image = serializers.PrimaryKeyRelatedField(
        queryset=RunObjetGroupImage.objects.all()
    )

    class Meta:
        model = models.MeasuringPointImage
        fields = ("id", "point_location", "run_object_group_image")

        read_only_fields = ("id",)


class MeasuringPointImageReadonlySerializer(serializers.ModelSerializer):
    run_object_group_image = RunObjectGroupImageSerializer()

    class Meta:
        model = models.MeasuringPointImage
        fields = ("id", "point_location", "run_object_group_image")

        read_only_fields = ("id", "point_location", "run_object_group_image")


class MeasuringPointsSerializer(serializers.ModelSerializer):
    image = MeasuringPointImageReadonlySerializer(read_only=True)

    class Meta:
        model = models.MeasuringPoint
        fields = ("id", "name", "run", "object_group", "comments", "image")
        read_only_fields = ("run", "image")
