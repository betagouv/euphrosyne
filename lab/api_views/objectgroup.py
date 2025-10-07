import logging

from rest_framework import authentication, generics
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from ..objects import ObjectGroup, ObjectProviderError, fetch_partial_objectgroup
from . import serializers

logger = logging.getLogger(__name__)


@api_view(["POST"])
@authentication_classes([authentication.SessionAuthentication])
@permission_classes([IsAdminUser])
def get_eros_object(request):
    """Fetch object from Eros."""
    c2rmf_id = request.data["query"]
    try:
        obj = fetch_partial_objectgroup("c2rmf", c2rmf_id)
    except ObjectProviderError as error:
        logger.error(
            "An error occured when importing data from Eros.\nID: %s\nError: %s",
            c2rmf_id,
            error,
        )
        obj = None
    if not obj:
        raise NotFound("Object with this C2RMF ID was not found.")
    return Response({"c2rmf_id": obj["c2rmf_id"], "label": obj["label"]})


class ObjectGroupCreateView(IsAdminUser, generics.CreateAPIView):
    serializer_class = serializers.ObjectGroupCreateSerializer
    queryset = ObjectGroup.objects.all()

    def perform_create(self, serializer):
        serializer.save(object_count=1)
