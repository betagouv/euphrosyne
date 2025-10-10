import logging
import typing
from abc import ABC, abstractmethod

import requests

from ..models import ObjectGroup


class PartialObject(typing.TypedDict):
    """Partial object data structure."""

    label: str


class ObjectProviderError(requests.RequestException):
    """Base exception for object provider errors."""


class ObjectProvider(ABC):
    """Abstract base class for art object data providers."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch_partial_data(self, object_id: str) -> PartialObject | None:
        """Fetch object data with minimum information to save it to DB.

        Args:
            object_id: The unique identifier for the object in the provider system

        Returns:
            Dictionary containing at minimum the object_id and label,
            or None if not found

        Raises:
            ObjectProviderError: If there's an error fetching the data
        """

    @abstractmethod
    def fetch_full_object(
        self, object_id: str, object_group: ObjectGroup | None = None
    ) -> ObjectGroup | None:
        """Fetch object data with full information to display it.

        Args:
            object_id: The unique identifier for the object in the provider system
            object_group: Optional existing ObjectGroup instance to update
                (but does not save to DB)

        Returns:
            ObjectGroup instance with full data, or None if not found

        Raises:
            ObjectProviderError: If there's an error fetching the data
        """

    @abstractmethod
    def construct_image_url(self, path: str) -> str:
        """Construct image URL from provider-specific path.

        Args:
            path: Provider-specific path to the image

        Returns:
            Full URL to access the image
        """

    def _handle_http_error(
        self, error: requests.RequestException, object_id: str
    ) -> None:
        """Common HTTP error handling for all providers."""
        self.logger.error("HTTP error when fetching object %s: %s", object_id, error)
        raise ObjectProviderError from error

    def _handle_general_error(self, error: Exception, object_id: str) -> None:
        """Common error handling for all providers."""
        self.logger.error("Error when fetching object %s: %s", object_id, error)
        raise ObjectProviderError from error
