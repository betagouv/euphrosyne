from .. import queries
from ._mock import BASE_SEARCH_PARAMS, BASE_SEARCH_PARAMS_RELATED_QUERY


def test_build_query_with_all_params():
    query = queries.Query().build_query(BASE_SEARCH_PARAMS)
    assert query == BASE_SEARCH_PARAMS_RELATED_QUERY


def test_build_query_with_no_params_return_match_all():
    query = queries.Query().build_query({})
    assert query == {
        "query": {"match_all": {}},
        "sort": [{"created": {"order": "desc"}}],
        "from": 0,
        "size": 10,
    }


def test_terms_agg_query():
    query = queries.terms_agg("materials", query="or", exclude=["argent"])
    assert query == {
        "size": 0,
        "aggs": {
            "materials": {
                "terms": {
                    "field": "materials",
                    "include": ".*or.*",
                    "exclude": "argent",
                }
            }
        },
    }


def test_date_historiogram_agg_query():
    query = queries.date_historiogram_agg("created", "year")
    assert query == {
        "size": 0,
        "aggs": {
            "created": {
                "date_histogram": {"field": "created", "calendar_interval": "year"}
            }
        },
    }
