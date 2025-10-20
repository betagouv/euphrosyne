import enum
import typing
from functools import lru_cache

import requests

from lab.thesauri.models import Era, Period

from ..models import ObjectGroup
from .base import ObjectProvider
from .registry import registry


class POPDatabases(enum.StrEnum):
    MERIMEE = "merimee"
    PALISSY = "palissy"
    MEMOIRE = "memoire"
    JOCONDE = "joconde"
    MNR = "mnr"
    MUSEO = "museo"
    ENLUMINURES = "enluminures"
    AUTOR = "autor"


SEARCHED_DATABASES = ",".join([POPDatabases.JOCONDE.value, POPDatabases.PALISSY.value])
POP_BASE_URL = f"https://api.pop.culture.gouv.fr/search/{SEARCHED_DATABASES}/_msearch"

POP_IMAGE_URL = "https://pop-perf-assets.s3.gra.io.cloud.ovh.net"


class ObjectData(typing.TypedDict):
    POP_COORDONNEES: dict
    MILU: str
    CONTACT: str
    ETAT: str
    LOCA: str
    PDAT: str
    HIST: str
    VIDEO: typing.List[str]
    TICO: str
    LVID: str
    PREP: str
    DESC: str
    RANG: str
    DIFFU: str
    HISTORIQUE: typing.List[typing.Any]
    COMM: str
    IMAGE: str
    TITR: str
    PRODUCTEUR: str
    INSC: typing.List[typing.Any]
    DREP: str
    LABEL: str
    POP_CONTIENT_GEOLOCALISATION: str
    DDPT: str
    DENO: typing.List[typing.Any]
    PUTI: str
    LABO: str
    IMG: typing.List[str]
    CONTIENT_IMAGE: str
    UTIL: typing.List[typing.Any]
    NSDA: str
    POP_IMPORT: typing.List[typing.Any]
    DECV: str
    AUTR: typing.List[str]
    PEOC: typing.List[typing.Any]
    REGION: str
    TECH: typing.List[str]
    DACQ: str
    GENE: typing.List[typing.Any]
    NOMOFF: str
    POP_FLAGS: typing.List[typing.Any]
    DATA: str
    PDEC: str
    DESY: str
    MILL: typing.List[typing.Any]
    REFMEM: typing.List[typing.Any]
    VILLE_M: str
    REFMER: typing.List[typing.Any]
    REFMIS: str
    LARC: str
    DPT: str
    PERI: typing.List[str]
    DIMS: str
    DOMN: typing.List[str]
    BIBL: str
    BASE: str
    MANQUANT: typing.List[typing.Any]
    COOR: str
    INV: str
    DMAJ: str
    EXPO: str
    DMIS: str
    REPR: typing.List[typing.Any]
    MOSA: str
    DATION: str
    REDA: typing.List[typing.Any]
    ONOM: typing.List[typing.Any]
    LIEUX: typing.List[typing.Any]
    ECOL: typing.List[str]
    PINS: str
    PERU: typing.List[typing.Any]
    DEPO: typing.List[typing.Any]
    LOCA3: str
    LOCA2: str
    COPY: str
    SREP: typing.List[typing.Any]
    MANQUANT_COM: str
    EPOQ: typing.List[typing.Any]
    ATTR: str
    PLIEUX: str
    MUSEO: str
    REFPAL: typing.List[typing.Any]
    STAT: typing.List[str]
    REF: str
    REFIM: str
    APPL: str
    PAUT: str
    WWW: typing.List[str]
    APTN: str
    MSGCOM: str
    PHOT: str
    ADPT: str
    RETIF: str
    GEOHI: typing.List[typing.Any]
    TOUT: str


class POPProvider(ObjectProvider):
    """POP provider implementation."""

    @lru_cache
    def _fetch_raw_data(self, provider_id: str) -> ObjectData | None:
        """Fetch raw object data from POP."""
        try:
            body = (
                '{"preference":"res"}\n{"query":{"bool":{"must":[{"bool":{"should":[{"term":{"REF.keyword":"%s"}}]}},{"match_all":{}}]}},"size":25,"from":0}'  # pylint: disable=line-too-long
                % provider_id
            )
            response = requests.post(
                POP_BASE_URL,
                data=body,
                headers={
                    "Content-Type": "application/x-ndjson",
                },
                timeout=5,
            )
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as error:
            self._handle_http_error(error, provider_id)

        if response.status_code == 200:
            data = response.json()
            if not data["responses"][0]["hits"]["hits"]:
                return None
            return data["responses"][0]["hits"]["hits"][0]["_source"]
        return None

    def fetch_partial_data(self, object_id: str):
        """Fetch object data with minimum information to save it to DB."""
        data = self._fetch_raw_data(object_id)
        if data:
            return {"label": data["TITR"]}
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
        updated_og.label = data["TITR"]
        if data.get("PERI"):
            dating_label = ", ".join(data["PERI"])
            updated_og.dating_period = Period(label=dating_label)
        if data.get("EPOQ"):
            era_label = ", ".join(data["EPOQ"])
            updated_og.dating_era = Era(label=era_label)
        updated_og.inventory = data.get("INV", "")
        updated_og.materials = data.get("TECH", [])
        return updated_og

    def fetch_object_image_urls(self, object_id: str) -> list[str]:
        """Fetch list of image URLs for the given object ID."""
        data = self._fetch_raw_data(object_id)
        if not data or "IMG" not in data:
            return []
        return [self.construct_image_url(img) for img in data["IMG"]]

    def construct_image_url(self, path: str) -> str:
        return f"{POP_IMAGE_URL}/{path}"


registry.register("pop", POPProvider)
