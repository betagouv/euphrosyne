import csv
import io
from dataclasses import asdict
from typing import Collection, Optional

import pytest

from ..csv_upload import parse_csv


def _generate_csv(
    rows: Collection[dict[str, str]], fields: Optional[Collection[str]] = None
):
    fields = fields or ("label", "inventory", "collection")
    file = io.StringIO()
    csv_writer = csv.DictWriter(file, fields)
    csv_writer.writeheader()
    csv_writer.writerows(rows)
    file.seek(0)
    return file


def test_parse_csv():
    rows = (
        {"label": "Objet 1", "inventory": "ABC", "collection": "DEF"},
        {"label": "Objet 2", "inventory": "DGT", "collection": "GHI"},
        {"label": "Objet 3", "inventory": "ZDT", "collection": "OPS"},
    )
    file = _generate_csv(rows)
    objects = list(parse_csv(file))

    assert len(objects) == 3
    for obj in objects:
        assert asdict(obj) in rows


def test_parse_csv_raises_with_unknown_property():
    rows = (
        {
            "label": "Objet 1",
            "inventory": "ABC",
            "collection": "DEF",
            "UNKNOWN_PROP": "NA",
        },
    )
    file = _generate_csv(
        rows, fields=("label", "inventory", "collection", "UNKNOWN_PROP")
    )
    with pytest.raises(TypeError):
        list(parse_csv(file))
