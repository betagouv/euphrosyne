import os
import typing
from functools import lru_cache

import requests
from django.conf import settings

from lab.thesauri.models import Era

from ..models import ObjectGroup
from .base import ObjectProvider
from .registry import registry

EROS_BASE_URL = "http://eros.c2rmf.fr"


class ErosImage(typing.TypedDict):
    """EROS image data structure."""

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
    """EROS object data structure."""

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


class ErosProvider(ObjectProvider):
    """C2RMF EROS provider implementation."""

    @lru_cache
    def _fetch_raw_data(self, eros_id: str) -> ErosData | None:
        """Fetch raw object data from EROS."""
        token = os.environ["EROS_HTTP_TOKEN"]
        try:
            request = requests.get(
                f"{EROS_BASE_URL}/rails/oeuvres/{eros_id}.json?token={token}",
                timeout=5,
            )
            request.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as error:
            self._handle_http_error(error, eros_id)

        if request.status_code == 200:
            return request.json()
        return None

    def fetch_partial_data(self, object_id: str):
        """Fetch object data with minimum information to save it to DB."""
        data = self._fetch_raw_data(object_id)
        if data:
            return {"label": data["title"]}
        return None

    def fetch_full_object(
        self, object_id: str, object_group: ObjectGroup | None = None
    ) -> ObjectGroup | None:
        """Fetch object data with full information to display it."""
        updated_og = object_group or ObjectGroup()
        data = self._fetch_raw_data(object_id)
        if not data:
            return object_group

        updated_og.object_count = 1
        updated_og.label = data["title"]
        if data.get("dtfrom") or data.get("period"):
            dating_label = data.get("dtfrom") or data["period"]
            updated_og.dating_era = Era(label=dating_label)
        updated_og.collection = data.get("collection") or ""
        updated_og.inventory = data.get("inv") or ""
        updated_og.materials = (data.get("support") or "").split(" / ")
        return updated_og

    def fetch_object_image_urls(self, object_id: str) -> list[str]:
        """Fetch list of image URLs for the given object ID."""
        data = self._fetch_raw_data(object_id)
        if not data or "images" not in data:
            return []
        return [
            self.construct_image_url(f"{object_id}/{image['filmnbr']}")
            for image in data["images"]
        ]

    def construct_image_url(self, path: str) -> str:
        """Construct image URL from C2RMF path."""
        # pylint: disable=import-outside-toplevel
        from euphro_auth.jwt.tokens import EuphroToolsAPIToken

        eros_id, image_id = path.split("/")
        if eros_id.startswith("C2RMF"):
            image_category = f"pyr-{eros_id[:6]}"
        elif eros_id.startswith("F"):
            image_category = f"pyr-{eros_id[:2]}"
        else:
            image_category = "pyr-FZ"

        eros_base_url = (
            settings.EROS_BASE_IMAGE_URL or f"{settings.EUPHROSYNE_TOOLS_API_URL}/eros"
        )

        url = f"{eros_base_url}/iiif/{image_category}/{eros_id}/{image_id}.tif/full/500,/0/default.jpg"  # pylint: disable=line-too-long

        # Add token to the URL if using EROS direct URL. Else we use the EuphroTools API
        # proxy which includes the token in the request headers.
        if settings.EROS_BASE_IMAGE_URL:
            token = os.environ["EROS_HTTP_TOKEN"]
        else:
            token = EuphroToolsAPIToken.for_euphrosyne().access_token
        return f"{url}?token={token}"


# Register the EROS provider
registry.register("eros", ErosProvider)
