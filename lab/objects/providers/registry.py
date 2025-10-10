from typing import Type

from .base import ObjectProvider


class ProviderRegistry:
    """Registry for object providers."""

    _providers: dict[str, Type[ObjectProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[ObjectProvider]) -> None:
        """Register a provider class with a given name.

        Args:
            name: The provider name (e.g., 'eros', 'pop')
            provider_class: The provider class implementing ObjectProvider
        """
        cls._providers[name] = provider_class

    @classmethod
    def get_provider(cls, name: str) -> ObjectProvider:
        """Get a provider instance by name.

        Args:
            name: The provider name

        Returns:
            Provider instance

        Raises:
            KeyError: If provider name is not registered
        """
        if name not in cls._providers:
            raise KeyError(f"Provider '{name}' is not registered")
        return cls._providers[name]()

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names."""
        return list(cls._providers.keys())


# Global registry instance
registry = ProviderRegistry()
