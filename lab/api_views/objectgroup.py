import logging

from drf_spectacular.utils import extend_schema
from rest_framework import authentication, generics
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from ..objects import (
    ObjectGroup,
    ObjectProviderError,
    fetch_object_image_urls,
    fetch_partial_objectgroup,
)
from . import serializers

logger = logging.getLogger(__name__)


@api_view(["POST"])
@authentication_classes([authentication.SessionAuthentication])
@permission_classes([IsAdminUser])
def get_object_from_provider(request, provider_name: str):
    """Fetch object from external provider."""
    external_reference_id = request.data["query"]
    try:
        obj = fetch_partial_objectgroup(provider_name, external_reference_id)
    except ObjectProviderError as error:
        logger.error(
            "An error occurred when importing data from %s.\nID: %s\nError: %s",
            provider_name,
            external_reference_id,
            error,
        )
        obj = None
    if not obj:
        raise NotFound("Object with this external reference ID was not found.")
    return Response(
        {"external_reference_id": external_reference_id, "label": obj["label"]}
    )


@extend_schema(
    responses={200: serializers.GetObjectImageFromProviderResponseSerializer},
)
@api_view(["GET"])
@authentication_classes([authentication.SessionAuthentication])
@permission_classes([IsAdminUser])
def get_object_images_from_provider(request: Request, provider_name: str):
    """Fetch object images from external provider."""
    external_reference_id = request.query_params.get("object_id")
    if not external_reference_id:
        return Response({"detail": "Missing 'object_id' query parameter"}, status=400)
    try:
        images = fetch_object_image_urls(provider_name, external_reference_id)
    except ObjectProviderError as error:
        logger.error(
            "An error occurred when searching for images from %s.\nID: %s\nError: %s",
            provider_name,
            external_reference_id,
            error,
        )
        images = []
    return Response({"images": images})


@api_view(["POST"])
@authentication_classes([authentication.SessionAuthentication])
@permission_classes([IsAdminUser])
def get_eros_object(request):
    """DEPRECATED. Use get_object_from_provider with provider_name='eros' instead.
    Fetch object from Eros."""
    import sentry_sdk  # pylint: disable=import-outside-toplevel

    sentry_sdk.capture_message(
        "Deprecated API endpoint called: lab/api_views/objectgroup.py/get_eros_object",
        level="warning",
    )

    c2rmf_id = request.data["query"]
    try:
        obj = fetch_partial_objectgroup("eros", c2rmf_id)
    except ObjectProviderError as error:
        logger.error(
            "An error occurred when importing data from Eros.\nID: %s\nError: %s",
            c2rmf_id,
            error,
        )
        obj = None
    if not obj:
        raise NotFound("Object with this EROS ID was not found.")
    return Response({"c2rmf_id": c2rmf_id, "label": obj["label"]})


class ObjectGroupCreateView(IsAdminUser, generics.CreateAPIView):
    serializer_class = serializers.ObjectGroupCreateSerializer
    queryset = ObjectGroup.objects.all()

    def perform_create(self, serializer):
        serializer.save(object_count=1)
