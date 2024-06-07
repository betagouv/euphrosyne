# pylint: disable=line-too-long

import datetime

BASE_SEARCH_PARAMS = {
    "q": "q",
    "status": "Status.DATA_AVAILABLE",
    "materials": ["material1", "material2"],
    "period_ids": ["period1", "period2"],
    "category": "project",
    "c2rmf_id": "c2rmf_id",
    "created_from": datetime.datetime(2021, 1, 1).strftime("%Y-%m-%d"),
    "created_to": datetime.datetime(2021, 12, 31).strftime("%Y-%m-%d"),
    "location": {
        "top_left": {"lat": 1.0, "lon": 1.0},
        "bottom_right": {"lat": 1.0, "lon": 1.0},
    },
    "collection": "collection",
    "inventory": "inventory",
    "is_data_available": True,
    "_from": 0,
    "size": 10,
    "sort": "asc",
}


BASE_SEARCH_PARAMS_RELATED_QUERY = {
    "query": {
        "bool": {
            "filter": [{"term": {"category": "project"}}],
            "must": [
                {
                    "multi_match": {
                        "query": "q",
                        "fields": [
                            "name",
                            "collections",
                            "collection",
                            "materials",
                        ],
                    }
                },
                {"term": {"status": "Status.DATA_AVAILABLE"}},
                {"terms": {"materials": ["material1", "material2"]}},
                {"terms": {"dating_theso_huma_num_parent_ids": ["period1", "period2"]}},
                {"term": {"c2rmf_id": "c2rmf_id"}},
                {
                    "range": {
                        "created": {
                            "gte": "2021-01-01",
                            "lte": datetime.datetime.max,
                        },
                    },
                },
                {
                    "range": {
                        "created": {
                            "gte": datetime.datetime.min,
                            "lte": "2021-12-31",
                        },
                    },
                },
                {
                    "geo_bounding_box": {
                        "discovery_place_points": {
                            "top_left": {"lat": 1.0, "lon": 1.0},
                            "bottom_right": {"lat": 1.0, "lon": 1.0},
                        }
                    }
                },
                {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": "collection",
                                    "fields": [
                                        "collection",
                                        "project_page_data.object_groups.collection",
                                        "project_page_data.object_groups.objects.collection",
                                    ],
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {"terms": {"collection": ["collection"]}},
                                        {
                                            "term": {
                                                "project_page_data.object_groups.collection": "collection"
                                            }
                                        },
                                        {
                                            "term": {
                                                "project_page_data.object_groups.objects.collection": "collection"
                                            }
                                        },
                                    ]
                                }
                            },
                        ]
                    }
                },
                {
                    "bool": {
                        "should": [
                            {"terms": {"inventory_numbers": ["inventory"]}},
                            {
                                "term": {
                                    "project_page_data.object_groups.inventory": "inventory"
                                }
                            },
                            {
                                "term": {
                                    "project_page_data.object_groups.objects.inventory": "inventory"
                                }
                            },
                        ]
                    }
                },
                {"term": {"is_data_available": True}},
            ],
        }
    },
    "from": 0,
    "size": 10,
}
