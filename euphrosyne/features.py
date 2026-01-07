"""
Feature registry for optional Euphrosyne modules.
"""

from __future__ import annotations

import os
from typing import Iterable, List

FEATURE_APPS = {
    "data_request": [
        "data_request",
    ],
    "lab_notebook": [
        "lab_notebook",
    ],
    "radiation_protection": [
        "radiation_protection.apps.RadiationProtectionConfig",
    ],
}


def _parse_feature_list(raw_value: str) -> List[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def enabled_features() -> List[str]:
    raw_features = os.getenv("EUPHROSYNE_FEATURES")
    if raw_features is not None:
        if not raw_features.strip():
            return []
        requested = _parse_feature_list(raw_features)
        return [feature for feature in requested if feature in FEATURE_APPS]
    return list(FEATURE_APPS.keys())


def add_feature_apps(installed_apps: Iterable[str]) -> List[str]:
    updated_apps = list(installed_apps)
    for feature in enabled_features():
        updated_apps += FEATURE_APPS[feature]
    return updated_apps
