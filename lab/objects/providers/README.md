# Art Object Providers

This package provides an abstraction layer for importing art objects from different databases/APIs.

## Architecture

- **Base Class**: `ObjectProvider` - Abstract base class defining the interface
- **Registry**: Centralized provider registration and discovery
- **API**: Unified functions for accessing any provider
- **Providers**: Implementation for specific databases (Eros, POP, etc.)

## Usage

### Using the Unified API (Recommended)

```python
from lab.objects.providers import (
    fetch_partial_objectgroup,
    fetch_full_objectgroup,
    construct_image_url,
    list_available_providers
)

# List all available providers
providers = list_available_providers()
# ['eros', 'pop']

# Fetch minimal data for DB storage
partial_data = fetch_partial_objectgroup('eros', 'C2RMF65980')
# {'label': 'Majolique'}

# Fetch full object data
full_object = fetch_full_objectgroup('eros', 'C2RMF65980')
# Returns ObjectGroup instance with all metadata

# Construct image URL
image_url = construct_image_url('eros', 'C2RMF65980/12345')
# Returns full IIIF image URL with authentication
```

## Adding New Providers

1. Create a new provider class inheriting from `ObjectProvider`:

```python
from .base import ObjectProvider
from .registry import registry

class MyProvider(ObjectProvider):
    def fetch_partial_data(self, object_id: str) -> PartialObject | None:
        # Implement fetching logic
        pass

    def fetch_full_object(self, object_id: str, obj_group=None) -> ObjectGroup | None:
        # Implement full object fetching
        pass

    def construct_image_url(self, path: str) -> str:
        # Implement image URL construction
        pass

# Register the provider
registry.register('my_provider', MyProvider)
```

2. Import your provider module to register it:

```python
# In providers/__init__.py
from . import my_provider  # noqa: F401
```

## Available Providers

Providers are available in this package and registered in \_\_init\_\_ module.

## Error Handling

All providers use a common error handling pattern:

```python
from lab.objects.providers.base import ObjectProviderError

try:
    data = fetch_partial_objectgroup('eros', 'invalid_id')
except ObjectProviderError as e:
    # Handle provider-specific errors
    pass
```
