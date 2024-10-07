from rest_framework import serializers

from ...models import RunNotebook


class RunNotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunNotebook
        fields = ("comments",)
