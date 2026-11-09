from drf_spectacular.plumbing import resolve_type_hint
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .client import CatalogClient
from .queries import QueryParams

# Generated from the TypedDict the search code is typed with, so that the
# schema given to the WAF cannot drift from it.
CATALOG_SEARCH_REQUEST = {"application/json": resolve_type_hint(QueryParams)}


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def list_all_items(request):
    """Catalog items listing endpoint"""
    results = CatalogClient().list_all_items()
    return Response(results)


@extend_schema(
    request=CATALOG_SEARCH_REQUEST,
    responses=OpenApiTypes.OBJECT,
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
    responses=OpenApiTypes.OBJECT,
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


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def aggregate_created(request):
    """Catalog aggregation endpoint"""
    results = CatalogClient().aggregate_date(
        "created",
        "year",
    )
    return Response(results)
