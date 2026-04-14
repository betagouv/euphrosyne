import typing
from functools import lru_cache

import requests

from lab.thesauri.models import Era, Period

from ..models import ObjectGroup
from .base import ObjectProvider, PartialObject
from .registry import registry

# pylint: disable=line-too-long
POP_BASE_URL = "https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/"

POP_IIF_MANIFEST_URL = (
    "https://api.pop.culture.gouv.fr/notices/joconde/{}/iiif/manifest"
)
POP_IMAGE_URL = "https://iiif.prd.cloud.culture.fr/iiif/3"


POPQueryParams = dict[str, str | int]


class ObjectData(typing.TypedDict):
    Reference: str
    Titre: typing.NotRequired[str | None]
    Denomination: typing.NotRequired[str | None]
    Appellation: typing.NotRequired[str | None]
    Epoque: typing.NotRequired[str | None]
    Periode_de_creation: typing.NotRequired[str | None]
    Numero_inventaire: typing.NotRequired[str | None]
    Materiaux_techniques: typing.NotRequired[str | None]
    Lien_site_associe: typing.NotRequired[str | None]
    Source_de_la_representation: typing.NotRequired[str | None]


class POPDataResponse(typing.TypedDict):
    data: list[ObjectData]


class POPProvider(ObjectProvider):
    """POP provider implementation."""

    @lru_cache
    def _fetch_raw_data(self, object_id: str) -> ObjectData | None:
        """Fetch raw object data from POP."""
        params: POPQueryParams = {
            "Reference__exact": object_id,
            "page_size": 1,
        }
        try:
            response = requests.get(
                POP_BASE_URL,
                params=params,
                timeout=5,
            )
            response.raise_for_status()
        except (
            requests.HTTPError,
            requests.ConnectionError,
            requests.Timeout,
        ) as error:
            self._handle_http_error(error, object_id)

        try:
            data: POPDataResponse = response.json()
        except ValueError as error:
            self._handle_general_error(error, object_id)
            return None

        records = data.get("data") or []
        return records[0] if records else None

    def fetch_partial_data(self, object_id: str):
        """Fetch object data with minimum information to save it to DB."""
        data = self._fetch_raw_data(object_id)
        if data:
            partial_data: PartialObject = {"label": self._resolve_label(data)}
            return partial_data
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
        updated_og.label = self._resolve_label(data)
        dating_label = data.get("Periode_de_creation", "")
        if dating_label:
            updated_og.dating_period = Period(label=dating_label)
        era_label = data.get("Epoque", "")
        if era_label:
            updated_og.dating_era = Era(label=era_label)
        updated_og.inventory = data.get("Numero_inventaire") or ""
        if materials_value := data.get("Materiaux_techniques"):
            updated_og.materials = materials_value.split(";")
        return updated_og

    def fetch_object_image_urls(self, object_id: str) -> list[str]:
        """Fetch list of image URLs for the given object ID."""
        manifest = self._fetch_iif_manifest(object_id)
        if not manifest:
            return []

        urls = []
        for canvas in manifest.get("items", []):
            for annotation_page in canvas.get("items", []):
                for annotation in annotation_page.get("items", []):
                    body = annotation.get("body", {})
                    if body.get("type") == "Image" and body.get("id"):
                        urls.append(body["id"])

        return urls

    def construct_image_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{POP_IMAGE_URL}{normalized_path}"

    def _fetch_iif_manifest(self, object_id: str):
        try:
            response = requests.get(
                POP_IIF_MANIFEST_URL.format(object_id),
                timeout=5,
            )
            response.raise_for_status()
        except (
            requests.HTTPError,
            requests.ConnectionError,
            requests.Timeout,
        ) as error:
            self._handle_http_error(error, object_id)

        try:
            return response.json()
        except ValueError as error:
            self._handle_general_error(error, object_id)
            return None

    @staticmethod
    def _resolve_label(data: ObjectData) -> str:
        return data.get("Titre") or data.get("Denomination") or ""


registry.register("pop", POPProvider)
