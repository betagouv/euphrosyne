import os
import typing
from functools import lru_cache
from typing import Any

import requests

from lab.thesauri.models import Era

from ..models import ObjectGroup


class ErosHTTPError(requests.RequestException):
    pass


class ErosImage(typing.TypedDict):
    filmnbr: str
    worknbr: str
    czone: str
    aimfilm: str
    technique: str
    dtfilm: str
    plfilm: str
    opfilm: str
    owner: str
    stock: str
    filmtype: str
    zone: str
    Xsize: str
    Ysize: str
    bands: str


class ErosData(typing.TypedDict):
    title: str
    local: str
    owner: str
    worknbr: str
    collection: str
    dtfrom: str
    dtto: str
    appel: str
    support: str
    technique: str
    height: str
    width: str
    workgroup: str
    srmf: str
    categ: str
    inv: str
    period: str
    images: typing.NotRequired[list[ErosImage]]


@lru_cache
def _fetch_object_group_from_eros(c2rmf_id: str) -> ErosData | None:
    """Fetch object group from EROS."""
    token = os.environ["EROS_HTTP_TOKEN"]
    try:
        request = requests.get(
            f"http://eros.c2rmf.fr/rails/oeuvres/{c2rmf_id}.json?token={token}",
            timeout=5,
        )
        request.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError) as error:
        raise ErosHTTPError from error
    if request.status_code == 200:
        return request.json()
    return None


def fetch_partial_objectgroup_from_eros(c2rmf_id: str) -> dict[str, Any] | None:
    """Fetch object group from EROS with minimum information to
    save it to DB."""
    data = _fetch_object_group_from_eros(c2rmf_id)
    if data:
        return {"c2rmf_id": c2rmf_id, "label": data["title"]}
    return None


def fetch_full_objectgroup_from_eros(
    c2rmf_id: str, object_group: ObjectGroup | None = None
) -> ObjectGroup | None:
    """Fetch object group from EROS with full information to display it.
    Update object_group instance if provided (but does not save it to DB)."""
    updated_og = object_group or ObjectGroup()
    data = _fetch_object_group_from_eros(c2rmf_id)
    if not data:
        return object_group

    updated_og.object_count = 1
    updated_og.c2rmf_id = c2rmf_id
    updated_og.label = data["title"]
    if data.get("dtfrom") or data.get("period"):
        dating_label = data.get("dtfrom") or data["period"]
        updated_og.dating_era = Era(label=dating_label)
    updated_og.collection = data.get("collection") or ""
    updated_og.inventory = data.get("inv") or ""
    updated_og.materials = (data.get("support") or "").split(" / ")
    return updated_og
