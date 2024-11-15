from rest_framework import serializers

from .. import models


class StandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Standard
        fields = ("label",)


class MeasuringPointStandardSerializer(serializers.ModelSerializer):
    class MeasuringPointStandardStandardSerializer(serializers.Serializer):
        label = serializers.CharField()

        def create(self, validated_data):
            raise NotImplementedError

        def update(self, instance, validated_data):
            raise NotImplementedError

    standard = MeasuringPointStandardStandardSerializer()

    class Meta:
        model = models.MeasuringPointStandard
        fields = ("standard", "id")
