from rest_framework import generics, serializers

from data_request.emails import send_data_request_created_email
from euphro_auth.jwt.authentication import EuphrosyneAdminJWTAuthentication
from lab.runs.models import Run

from .models import DataAccessEvent, DataRequest


class DataRequestSerializer(serializers.ModelSerializer):
    runs = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Run.objects.only_not_embargoed(),
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


class DataAccessEventSerializer(serializers.ModelSerializer):
    data_request = serializers.PrimaryKeyRelatedField(
        queryset=DataRequest.objects.all(),
        allow_empty=False,
    )

    class Meta:
        model = DataAccessEvent
        fields = ["data_request", "path"]


class DataAccessEventCreateAPIView(generics.CreateAPIView):
    queryset = DataAccessEvent.objects.all()
    serializer_class = DataAccessEventSerializer
    authentication_classes = [EuphrosyneAdminJWTAuthentication]
