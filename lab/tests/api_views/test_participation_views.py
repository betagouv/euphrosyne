from unittest import mock

from django.test import TestCase

from lab.api_views.participation import (
    MemberParticipationListCreateGroupView,
    MemberParticipationRetrieveUpdateDestroyGroupView,
)
from lab.api_views.serializers import (
    OnPremisesParticipationSerializer,
    ParticipationSerializer,
)
from lab.participations.models import Participation

from .. import factories


class TestMemberParticipationListCreateGroupView(TestCase):
    def test_queryset(self):
        view = MemberParticipationListCreateGroupView()
        assert view.queryset.model == Participation

    def test_serializer_class(self):
        view = MemberParticipationListCreateGroupView()
        assert view.serializer_class == ParticipationSerializer


class TestMemberParticipationRetrieveUpdateDestroyGroupView(TestCase):
    def test_queryset(self):
        view = MemberParticipationRetrieveUpdateDestroyGroupView()
        assert view.queryset.model == Participation

    def test_get_serializer_class_for_on_premises_participation(self):
        participation = factories.ParticipationFactory(on_premises=True)
        view = MemberParticipationRetrieveUpdateDestroyGroupView()
        view.kwargs = {"pk": participation.id}
        view.request = mock.MagicMock()

        # Mock get_object to return the participation
        with mock.patch.object(view, "get_object", return_value=participation):
            serializer_class = view.get_serializer_class()
            assert serializer_class == OnPremisesParticipationSerializer

    def test_get_serializer_class_for_remote_participation(self):
        participation = factories.ParticipationFactory(on_premises=False)
        view = MemberParticipationRetrieveUpdateDestroyGroupView()
        view.kwargs = {"pk": participation.id}
        view.request = mock.MagicMock()

        # Mock get_object to return the participation
        with mock.patch.object(view, "get_object", return_value=participation):
            serializer_class = view.get_serializer_class()
            assert serializer_class == ParticipationSerializer
