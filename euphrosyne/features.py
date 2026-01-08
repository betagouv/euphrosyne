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
    """
    Returns enabled features based on EUPHROSYNE_FEATURES env variable.

    Behavior:
    - If EUPHROSYNE_FEATURES is not set: all features enabled (default)
    - If set to empty string or whitespace: NO features enabled
    - If set to comma-separated list: only those features are enabled

    Returns:
        List of feature names that should be enabled
    """
    raw_features = os.getenv("EUPHROSYNE_FEATURES")
    if raw_features is not None:
        # Environment variable is explicitly set
        if not raw_features.strip():
            # Empty string: disable all features
            return []
        # Non-empty: parse and filter requested features
        requested = _parse_feature_list(raw_features)
        return [feature for feature in requested if feature in FEATURE_APPS]
    # Environment variable is not set: enable all features by default
    return list(FEATURE_APPS.keys())


def add_feature_apps(installed_apps: Iterable[str]) -> List[str]:
    updated_apps = list(installed_apps)
    for feature in enabled_features():
        updated_apps += FEATURE_APPS[feature]
    return updated_apps
