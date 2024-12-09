import logging
from functools import lru_cache

import requests
from requests import JSONDecodeError

from .models import Era, Period

logger = logging.getLogger(__name__)


@lru_cache
def fetch_parent_ids_from_id(theso_id: str, concept_id: str) -> list[str]:
    try:
        response = requests.get(
            # pylint: disable=line-too-long
            f"https://opentheso.huma-num.fr/openapi/v1/concept/{theso_id}/{concept_id}/expansion?way=top",
            headers={"Accept": "application/json"},
            timeout=5,
        )
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch parent ids from OpenTheso: %s", e)
        return []
    if not response.ok:
        logger.error(
            "Failed to fetch parent ids from OpenTheso: %s %s",
            response.status_code,
            response.text,
        )
        return []
    try:
        data = response.json()
    except JSONDecodeError as e:
        logger.error(
            "Failed to fetch parent ids from OpenTheso. Invalid JSON. %s\n%s",
            e,
            response.text,
        )
        return []
    if data and isinstance(data, dict):
        # We exclude the first item as it is common to all branches
        return [key.split("/")[-1] for key, _ in list(data.items())[1:]]
    logger.error(
        "Failed to fetch parent ids from OpenTheso. Invalid response. %s", response.text
    )
    return []


def fetch_era_parent_ids_from_id(concept_id: str):
    return fetch_parent_ids_from_id(Era.OPENTHESO_THESO_ID, concept_id)


def fetch_period_parent_ids_from_id(concept_id: str):
    return fetch_parent_ids_from_id(Period.OPENTHESO_THESO_ID, concept_id)
