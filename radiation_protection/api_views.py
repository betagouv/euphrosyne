from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers

from certification.certifications.models import QuizResult
from lab.api_views.permissions import IsLabAdminUser

from .certification import get_radioprotection_certification


class UserRadiationProtectionResultRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResult
        fields = ["id", "created"]


class UserRadiationProtectionResultRetrieveView(  # pylint: disable=too-many-ancestors
    generics.RetrieveAPIView,
):
    serializer_class = UserRadiationProtectionResultRetrieveSerializer
    permission_classes = [IsLabAdminUser]

    def get_queryset(self):
        return QuizResult.objects.filter_valid_results_for_user(
            user=get_user_model().objects.get(id=self.kwargs["user_id"]),
            certification=get_radioprotection_certification(),
        ).order_by("-created")

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
        )
