import dataclasses
import datetime
from typing import Literal, NotRequired, TypedDict

from lab.projects.models import Project


class GeoPoint(TypedDict):
    lat: float
    lon: float


class Location(TypedDict):
    top_left: NotRequired[GeoPoint]
    bottom_right: NotRequired[GeoPoint]
    top_right: NotRequired[GeoPoint]
    bottom_left: NotRequired[GeoPoint]


class QueryParams(TypedDict, total=False):
    q: str
    status: str
    materials: list[str]
    period_ids: list[str]
    category: Literal["project", "object"]
    c2rmf_id: str
    created_from: datetime.datetime
    created_to: datetime.datetime
    location: Location
    collection: str
    inventory: str
    is_data_available: bool
    _from: int
    size: int
    sort: Literal["asc", "desc"]


@dataclasses.dataclass
class Query:
    must: list[dict]
    filter: list[dict]

    def __init__(self):
        self.must = []
        self.filter = []

    def build_query(
        self,
        params: QueryParams,
        size: int = None,
        _from: int = None,
        sort: Literal["asc", "desc"] = None,
    ):
        self._process_params(params)
        if self.must or self.filter:
            query = {
                "query": {
                    "bool": {
                        "filter": self.filter,
                        "must": self.must,
                    },
                },
            }
        else:
            query = match_all_query()
            query["sort"] = _sort_expression("created", "desc")
        query = _paginate_query(query, size, _from)
        if sort:
            query["sort"] = _sort_expression("created", sort)
        return query

    def _process_params(self, params: QueryParams):
        """Process query params into ES query.
        Populates self.must and self.filter with query expressions."""
        for key, value in params.items():
            if (not isinstance(value, bool) and not value) or value is None:
                continue

            # Filter queries -- if we add more filters we could create match fn
            # like _match_param_to_filter
            if key == "category":
                self.filter.append(_category_filter(value))
                continue

            # Must queries
            query = self._match_param_to_query(key, value)
            if query:
                self.must.append(query)

    # pylint: disable=too-many-return-statements
    def _match_param_to_query(
        self,
        key: str,
        value: str | list[str] | datetime.datetime | bool | int | Location,
    ):
        match key:
            case "q":
                return _search_box_query(
                    value, fields=["name", "collections", "collection", "materials"]
                )
            case "status":
                return _status_query(value)
            case "materials":
                return _materials_query(value)
            case "period_ids":
                return _period_query(value)
            case "category":
                return _category_filter(value)
            case "c2rmf_id":
                return _c2rmf_id_query(value)
            case "created_from":
                return _created_query(created_from=value)
            case "created_to":
                return _created_query(created_to=value)
            case "location":
                return _discovery_place_query(value)
            case "collection":
                return _collection_query(value)
            case "inventory":
                return _inventory_query(value)
            case "is_data_available":
                return _is_data_available_query(value)


def match_all_query():
    return {
        "query": {
            "match_all": {},
        },
    }


def filter_query(
    params: QueryParams,
):
    size = params.pop("size", None)
    _from = params.pop("_from", None)
    sort = params.pop("sort", None)
    return Query().build_query(
        params,
        size=size,
        _from=_from,
        sort=sort,
    )


def terms_agg(field: str, query: str | None = None, exclude: list[str] | None = None):
    expr = {field: {"terms": {"field": field}}}
    if query:
        expr[field]["terms"]["include"] = f".*{query}.*"
    if exclude:
        expr[field]["terms"]["exclude"] = "|".join(exclude)
    return {"size": 0, "aggs": expr}


def date_historiogram_agg(field: str, interval: str):
    return {
        "size": 0,
        "aggs": {
            field: {
                "date_histogram": {
                    "field": field,
                    "calendar_interval": interval,
                }
            }
        },
    }


def _paginate_query(query: dict, size: int = None, _from: int = None):
    return {
        **query,
        "from": _from or 0,
        "size": size or 10,
    }


def _search_box_query(q: str, fields: list[str]):
    return {
        "multi_match": {
            "query": q,
            "fields": fields,
        },
    }


def _status_query(status: Project.Status):
    return _term_query("status", status)


def _materials_query(materials: list[str]):
    return _terms_query("materials", materials)


def _period_query(dating_ids: list[str]):
    return _terms_query("dating_theso_huma_num_parent_ids", dating_ids)


def _category_filter(category: Literal["project", "object"]):
    return _term_query("category", category)


def _c2rmf_id_query(c2rmf_id: str):
    return _term_query("c2rmf_id", c2rmf_id)


def _created_query(
    created_from: datetime.datetime = None, created_to: datetime.datetime = None
):
    return {
        "range": {
            "created": {
                "gte": (created_from or datetime.datetime.min),
                "lte": (created_to or datetime.datetime.max),
            },
        },
    }


def _is_data_available_query(is_data_available: bool):
    return _term_query("is_data_available", is_data_available)


# https:#opensearch.org/docs/latest/query-dsl/geo-and-xy/geo-bounding-box/
def _discovery_place_query(location: Location):
    return {
        "geo_bounding_box": {
            "discovery_place_points": {
                **location,
            },
        }
    }


def _collection_query(collection: str):
    return _should_query(
        _search_box_query(
            collection,
            [
                "collection",
                "project_page_data.object_groups.collection",
                "project_page_data.object_groups.objects.collection",
            ],
        ),
        _should_query(
            _terms_query("collection", [collection]),
            _term_query("project_page_data.object_groups.collection", collection),
            _term_query(
                "project_page_data.object_groups.objects.collection", collection
            ),
        ),
    )


def _inventory_query(inventory: str):
    return _should_query(
        _terms_query("inventory_numbers", [inventory]),
        _term_query("project_page_data.object_groups.inventory", inventory),
        _term_query("project_page_data.object_groups.objects.inventory", inventory),
    )


def _should_query(*queries: dict):
    return {
        "bool": {
            "should": [*queries],
        },
    }


def _terms_query(field: str, values: list[str]):
    return {
        "terms": {
            field: values,
        },
    }


def _term_query(field: str, value: str):
    return {
        "term": {
            field: value,
        },
    }


def _sort_expression(field: str, order: Literal["asc", "desc"]):
    exp = {
        field: {"order": order},
    }
    return [exp]
