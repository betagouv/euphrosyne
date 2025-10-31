from rest_framework import generics

from lab.participations.models import Participation

from . import serializers


class MemberParticipationListCreateGroupView(generics.ListCreateAPIView):
    """Base views for listing and creating participations in a project.
    Do not use directly, use derived classes."""

    queryset = Participation.objects.all()
    serializer_class = serializers.ParticipationSerializer


class MemberParticipationRetrieveUpdateDestroyGroupView(
    generics.RetrieveUpdateDestroyAPIView
):
    """Base views for listing and creating participations in a project.
    Do not use directly, use derived classes."""

    queryset = Participation.objects.all()
    serializer_class = serializers.ParticipationSerializer

    def get_serializer_class(self):
        participation = self.get_object()
        if participation.on_premises:
            return serializers.OnPremisesParticipationSerializer
        return serializers.ParticipationSerializer
