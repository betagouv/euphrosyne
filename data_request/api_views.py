from rest_framework import generics, serializers

from data_request.emails import send_data_request_created_email

from .models import DataRequest


class DataRequestSerializer(serializers.ModelSerializer):
    runs = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=DataRequest.runs.rel.model.objects.all(),  # type: ignore[attr-defined] # pylint: disable=no-member
        allow_empty=False,
    )

    class Meta:
        model = DataRequest
        fields = [
            "user_email",
            "user_first_name",
            "user_last_name",
            "user_institution",
            "description",
            "runs",
        ]


class DataRequestCreateAPIView(generics.CreateAPIView):
    queryset = DataRequest.objects.all()
    serializer_class = DataRequestSerializer

    def perform_create(self, serializer: DataRequestSerializer):
        super().perform_create(serializer)
        send_data_request_created_email(serializer.instance.user_email)
