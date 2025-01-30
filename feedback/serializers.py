# pylint: disable=abstract-method
from rest_framework import serializers


class FeedbackAttachmentSerializer(serializers.Serializer):
    content_type = serializers.CharField(max_length=255)
    data = serializers.FileField()  # Change to FileField
    filename = serializers.CharField(max_length=255)


class FeedbackFormSerializer(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField()
    name = serializers.CharField(max_length=255)
