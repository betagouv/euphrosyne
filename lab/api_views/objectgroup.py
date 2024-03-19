import logging

from rest_framework import authentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from ..objects.c2rmf import ErosHTTPError, fetch_partial_objectgroup_from_eros

logger = logging.getLogger(__name__)


@api_view(["POST"])
@authentication_classes([authentication.SessionAuthentication])
@permission_classes([IsAdminUser])
def get_eros_object(request):
    """Fetch object from Eros."""
    c2rmf_id = request.data["query"]
    try:
        obj = fetch_partial_objectgroup_from_eros(c2rmf_id)
    except ErosHTTPError as error:
        logger.error(
            "An error occured when importing data from Eros.\nID: %s\nResponse: %s",
            c2rmf_id,
            error.response,
        )
        obj = None
    if not obj:
        raise NotFound("Object with this C2RMF ID was not found.")
    return Response({"c2rmf_id": obj["c2rmf_id"], "label": obj["label"]})
