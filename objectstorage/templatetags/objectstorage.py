from django import template
from django.core.files.storage import storages

register = template.Library()


@register.simple_tag
def objectstorage(path):
    """
    Returns the URL for a file stored in the objectstorage backend.

    Usage: {% objectstorage "path/to/file.jpg" %}
    """
    return storages["objectstorage"].url(path)
