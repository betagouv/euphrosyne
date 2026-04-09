import typing
from functools import lru_cache

import requests

from lab.thesauri.models import Era, Period

from ..models import ObjectGroup
from .base import ObjectProvider
from .registry import registry

POP_RESOURCE_ID = "7e3307c2-f2ff-455c-bbca-bb6f11aec7bb"
POP_BASE_URL = f"https://tabular-api.data.gouv.fr/api/resources/{POP_RESOURCE_ID}/data/"

POP_IMAGE_URL = "https://pop-perf-assets.s3.gra.io.cloud.ovh.net"


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
    def _fetch_raw_data(self, provider_id: str) -> ObjectData | None:
        """Fetch raw object data from POP."""
        try:
            response = requests.get(
                POP_BASE_URL,
                params={
                    "Reference__exact": provider_id,
                    "page_size": 1,
                },
                timeout=5,
            )
            response.raise_for_status()
        except (
            requests.HTTPError,
            requests.ConnectionError,
            requests.Timeout,
        ) as error:
            self._handle_http_error(error, provider_id)

        try:
            data: POPDataResponse = response.json()
        except ValueError as error:
            self._handle_general_error(error, provider_id)
            return None

        records = data.get("data") or []
        return records[0] if records else None

    @staticmethod
    def _split_values(value: str | None) -> list[str]:
        if not value:
            return []
        return [v.strip() for v in value.split(";") if v.strip()]

    @staticmethod
    def _resolve_label(data: ObjectData, object_id: str) -> str:
        return (
            (data.get("Titre") or "").strip()
            or (data.get("Denomination") or "").strip()
            or (data.get("Appellation") or "").strip()
            or object_id
        )

    def fetch_partial_data(self, object_id: str):
        """Fetch object data with minimum information to save it to DB."""
        data = self._fetch_raw_data(object_id)
        if data:
            return {"label": self._resolve_label(data, object_id)}
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
        updated_og.label = self._resolve_label(data, object_id)
        periods = self._split_values(data.get("Periode_de_creation"))
        if periods:
            dating_label = ", ".join(periods)
            updated_og.dating_period = Period(label=dating_label)
        eras = self._split_values(data.get("Epoque"))
        if eras:
            era_label = ", ".join(eras)
            updated_og.dating_era = Era(label=era_label)
        updated_og.inventory = data.get("Numero_inventaire") or ""
        updated_og.materials = self._split_values(data.get("Materiaux_techniques"))
        return updated_og

    def fetch_object_image_urls(self, object_id: str) -> list[str]:
        """Fetch list of image URLs for the given object ID."""
        data = self._fetch_raw_data(object_id)
        if not data:
            return []
        # The tabular API does not expose POP IMG paths. Keep only direct URL
        # values when available in link fields.
        image_urls: list[str] = []
        for field_name in ("Lien_site_associe", "Source_de_la_representation"):
            value = data.get(field_name)
            if not value:
                continue
            for url in [item.strip() for item in value.split(";") if item.strip()]:
                if url.startswith(("http://", "https://")):
                    image_urls.append(url)
        return list(dict.fromkeys(image_urls))

    def construct_image_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{POP_IMAGE_URL}{normalized_path}"


registry.register("pop", POPProvider)
