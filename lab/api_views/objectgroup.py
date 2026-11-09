import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import authentication, generics
from rest_framework import serializers as drf_serializers
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

_FETCH_OBJECT_REQUEST = inline_serializer(
    "FetchObjectFromProviderRequest",
    fields={
        "query": drf_serializers.CharField(
            help_text="Object identifier in the provider database."
        ),
    },
)


@extend_schema(request=_FETCH_OBJECT_REQUEST, responses=OpenApiTypes.OBJECT)
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
    parameters=[
        OpenApiParameter(
            "object_id",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            description="Object identifier in the provider database.",
        ),
    ],
    responses=serializers.GetObjectImageFromProviderResponseSerializer,
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


class ObjectGroupCreateView(generics.CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.ObjectGroupCreateSerializer
    queryset = ObjectGroup.objects.all()

    def perform_create(self, serializer):
        serializer.save(object_count=1)
