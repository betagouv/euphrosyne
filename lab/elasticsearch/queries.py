import dataclasses
import datetime
from typing import Literal, NotRequired, TypedDict, cast

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
    status: Project.Status
    materials: list[str]
    dating_period_ids: list[str]
    dating_era_ids: list[str]
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
        size: int | None = None,
        _from: int | None = None,
        sort: Literal["asc", "desc"] | None = None,
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
                value = cast(Literal["project", "object"], value)
                self.filter.append(_category_filter(value))
                continue

            # Must queries
            query = self._match_param_to_query(key, params)
            if query:
                self.must.append(query)

    # pylint: disable=too-many-return-statements
    def _match_param_to_query(
        self,
        key: str,
        params: QueryParams,
    ):
        match key:
            case "q":
                return _search_box_query(
                    params["q"],
                    fields=["name", "collections", "collection", "materials"],
                )
            case "status":
                return _status_query(params["status"])
            case "materials":
                return _materials_query(params["materials"])
            case "dating_period_ids":
                return _dating_period_query(params["dating_period_ids"])
            case "dating_era_ids":
                return _dating_era_query(params["dating_era_ids"])
            case "category":
                return _category_filter(params["category"])
            case "c2rmf_id":
                return _c2rmf_id_query(params["c2rmf_id"])
            case "created_from":
                return _created_query(created_from=params["created_from"])
            case "created_to":
                return _created_query(created_to=params["created_to"])
            case "location":
                return _discovery_place_query(params["location"])
            case "collection":
                return _collection_query(params["collection"])
            case "inventory":
                return _inventory_query(params["inventory"])
            case "is_data_available":
                return _is_data_available_query(params["is_data_available"])


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


def _paginate_query(query: dict, size: int | None = None, _from: int | None = None):
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
    return _term_query("status", status)  # type: ignore


def _materials_query(materials: list[str]):
    return _terms_query("materials", materials)


def _dating_era_query(dating_ids: list[str]):
    return _terms_query("dating_era_theso_huma_num_parent_ids", dating_ids)


def _dating_period_query(dating_ids: list[str]):
    return _terms_query("dating_period_theso_huma_num_parent_ids", dating_ids)


def _category_filter(category: Literal["project", "object"]):
    return _term_query("category", category)


def _c2rmf_id_query(c2rmf_id: str):
    return _term_query("c2rmf_id", c2rmf_id)


def _created_query(
    created_from: datetime.datetime | None = None,
    created_to: datetime.datetime | None = None,
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


def _term_query(field: str, value: str | bool):
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
