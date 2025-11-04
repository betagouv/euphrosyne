from unittest import mock

from django.test import TestCase

from lab.api_views.participation import (
    LeaderParticipationCreateUpdateView,
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


class TestLeaderParticipationCreateUpdateView(TestCase):
    def test_queryset(self):
        """Test that the view queryset is Participation."""
        view = LeaderParticipationCreateUpdateView()
        assert view.queryset.model == Participation

    def test_serializer_class(self):
        """Test that the view uses OnPremisesParticipationSerializer."""
        view = LeaderParticipationCreateUpdateView()
        assert view.serializer_class == OnPremisesParticipationSerializer

    def test_perform_create_sets_is_leader_true(self):
        """Test that perform_create sets is_leader to True."""
        view = LeaderParticipationCreateUpdateView()
        view.request = mock.MagicMock()

        mock_serializer = mock.MagicMock()
        view.perform_create(mock_serializer)

        mock_serializer.save.assert_called_once_with(is_leader=True)

    def test_perform_update_sets_is_leader_true(self):
        """Test that perform_update sets is_leader to True."""
        view = LeaderParticipationCreateUpdateView()
        view.request = mock.MagicMock()

        mock_serializer = mock.MagicMock()
        view.perform_update(mock_serializer)

        mock_serializer.save.assert_called_once_with(is_leader=True)
