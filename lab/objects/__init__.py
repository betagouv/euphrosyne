"""
Objects package - Art object data management and provider API.

This package provides:
- Django models for art objects (ObjectGroup, Object, etc.)
- Provider API for fetching data from external sources (EROS, POP, etc.)
"""

# Import providers to register them
from . import providers  # noqa: F401
from .models import (  # noqa: F401
    Location,
    Object,
    ObjectGroup,
    ObjectGroupThumbnail,
    Period,
    RunObjetGroupImage,
)

# Export provider API for external use
from .providers import (  # noqa: F401
    ObjectProvider,
    ObjectProviderError,
    construct_image_url,
    fetch_full_objectgroup,
    fetch_object_image_urls,
    fetch_partial_objectgroup,
    list_available_providers,
)
