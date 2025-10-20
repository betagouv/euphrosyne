"""Unified API for art object providers."""

from lab.objects.providers.base import PartialObject

from ..models import ObjectGroup
from .registry import registry


def fetch_partial_objectgroup(
    provider_name: str, object_id: str
) -> PartialObject | None:
    """Fetch object data with minimum information to save it to DB.

    Args:
        provider_name: Name of the provider (e.g., 'eros', 'pop')
        object_id: The unique identifier for the object in the provider system

    Returns:
        Dictionary containing at minimum the object_id and label, or None if not found

    Raises:
        KeyError: If provider name is not registered
        ObjectProviderError: If there's an error fetching the data
    """
    provider = registry.get_provider(provider_name)
    return provider.fetch_partial_data(object_id)


def fetch_full_objectgroup(
    provider_name: str, object_id: str, object_group: ObjectGroup | None = None
) -> ObjectGroup | None:
    """Fetch object data with full information to display it.

    Args:
        provider_name: Name of the provider (e.g., 'eros', 'pop')
        object_id: The unique identifier for the object in the provider system
        object_group: Optional existing ObjectGroup instance to update
            (but does not save to DB)

    Returns:
        ObjectGroup instance with full data, or None if not found

    Raises:
        KeyError: If provider name is not registered
        ObjectProviderError: If there's an error fetching the data
    """
    provider = registry.get_provider(provider_name)
    return provider.fetch_full_object(object_id, object_group)


def fetch_object_image_urls(provider_name: str, object_id: str) -> list[str]:
    """Fetch list of image URLs for the given object ID.

    Args:
        provider_name: Name of the provider (e.g., 'eros', 'pop')
        object_id: The unique identifier for the object in the provider system
    Returns:
        List of image URLs, or empty list if not found
    """
    provider = registry.get_provider(provider_name)
    return provider.fetch_object_image_urls(object_id)


def construct_image_url(provider_name: str, path: str) -> str:
    """Construct image URL from provider-specific path.

    Args:
        provider_name: Name of the provider (e.g., 'eros', 'pop')
        path: Provider-specific path to the image

    Returns:
        Full URL to access the image

    Raises:
        KeyError: If provider name is not registered
    """
    provider = registry.get_provider(provider_name)
    return provider.construct_image_url(path)


def list_available_providers() -> list[str]:
    """List all available provider names."""
    return registry.list_providers()
