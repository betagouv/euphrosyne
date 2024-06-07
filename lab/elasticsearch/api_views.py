from rest_framework.decorators import api_view
from rest_framework.response import Response

from .client import CatalogClient


@api_view(["POST"])
def search(request):
    """Catalog search endpoint"""
    results = CatalogClient().search(**request.data)
    return Response(results)


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


@api_view(["GET"])
def aggregate_created(request):
    """Catalog aggregation endpoint"""
    results = CatalogClient().aggregate_date(
        "created",
        "year",
    )
    return Response(results)
