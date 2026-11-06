from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .client import CatalogClient

# Raw OpenSearch responses are returned as is.
_OPENSEARCH_RESPONSE = OpenApiResponse(
    OpenApiTypes.OBJECT, description="OpenSearch response."
)


_GeoPointSerializer = inline_serializer(
    "CatalogSearchGeoPoint",
    fields={"lat": serializers.FloatField(), "lon": serializers.FloatField()},
).__class__

# Mirrors lab.elasticsearch.queries.QueryParams (pagination key is "from").
CATALOG_SEARCH_REQUEST = inline_serializer(
    "CatalogSearchRequest",
    fields={
        "q": serializers.CharField(required=False, allow_blank=True),
        "status": serializers.CharField(required=False),
        "materials": serializers.ListField(
            child=serializers.CharField(), required=False
        ),
        "dating_period_ids": serializers.ListField(
            child=serializers.CharField(), required=False
        ),
        "dating_era_ids": serializers.ListField(
            child=serializers.CharField(), required=False
        ),
        "category": serializers.ChoiceField(
            choices=["project", "object"], required=False
        ),
        "c2rmf_id": serializers.CharField(required=False),
        # Passed as is to an OpenSearch range query: date or date-time.
        "created_from": serializers.CharField(required=False),
        "created_to": serializers.CharField(required=False),
        "location": inline_serializer(
            "CatalogSearchLocation",
            fields={
                "top_left": _GeoPointSerializer(required=False),
                "bottom_right": _GeoPointSerializer(required=False),
                "top_right": _GeoPointSerializer(required=False),
                "bottom_left": _GeoPointSerializer(required=False),
            },
            required=False,
        ),
        "collection": serializers.CharField(required=False),
        "inventory": serializers.CharField(required=False),
        "is_data_embargoed": serializers.BooleanField(required=False),
        "from": serializers.IntegerField(required=False, min_value=0),
        "size": serializers.IntegerField(required=False, min_value=0),
        "sort": serializers.ChoiceField(choices=["asc", "desc"], required=False),
    },
)


@extend_schema(responses={200: _OPENSEARCH_RESPONSE})
@api_view(["GET"])
def list_all_items(request):
    """Catalog items listing endpoint"""
    results = CatalogClient().list_all_items()
    return Response(results)


@extend_schema(
    request=CATALOG_SEARCH_REQUEST,
    responses={200: _OPENSEARCH_RESPONSE},
)
@api_view(["POST"])
def search(request):
    """Catalog search endpoint"""
    results = CatalogClient().search(**request.data)
    return Response(results)


@extend_schema(
    parameters=[
        OpenApiParameter(
            "field",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            description="Catalog field to aggregate, e.g. materials.",
        ),
        OpenApiParameter(
            "query",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Only keep terms containing this value.",
        ),
        OpenApiParameter(
            "exclude",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Comma-separated terms to exclude.",
        ),
    ],
    responses={
        200: _OPENSEARCH_RESPONSE,
        400: OpenApiResponse(description="Missing 'field' query parameter."),
    },
)
@api_view(["GET"])
def aggregate_field(request):
    """Catalog aggregation endpoint"""
    exclude = None
    if "field" not in request.query_params:
        return Response({"error": "'field' query param is required"}, status=400)
    if "exclude" in request.query_params:
        exclude = request.query_params["exclude"].split(",")
    results = CatalogClient().aggregate_terms(
        request.query_params["field"],
        query=request.query_params.get("query"),
        exclude=exclude,
    )
    return Response(results)


@extend_schema(responses={200: _OPENSEARCH_RESPONSE})
@api_view(["GET"])
def aggregate_created(request):
    """Catalog aggregation endpoint"""
    results = CatalogClient().aggregate_date(
        "created",
        "year",
    )
    return Response(results)
