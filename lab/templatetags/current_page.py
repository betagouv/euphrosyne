from django import template

register = template.Library()

# pylint: disable=line-too-long
@register.simple_tag
def is_current_page(href: str, *args, **kwargs) -> bool:
    """
    Check for a given urlencoded path if the wanted href
    is in the current page.

    If `exact_path` is set to True, `path`and `href` will be check for
    equality (default to false)

    Return `False` if the `href` or `path` is missing

    Parameters
    ----------
    value : str
        Link to the wanted page
    **kwargs :
        Dictionary of options

    Keyword Args
    ------------
        path : str
            URLEncoded path from the request
        exact_path : bool, optional
            Tell wether the `href` and the `path` must be equal (default=False)

    Example
    -------
    In a template, first cast the value in a template var to be able to use other var
    in the params
    ```python
    {% is_current_page href path=request.path|urlencoded exact_path=True as current_page %}
    ```

    Then you can simply check for the casted value
    ```python
    {% if current_page %}
        ...display stuff
    {% endif %}
    ```
    """

    if not href:
        return False

    path = kwargs["path"]
    exact_path = kwargs["exact_path"] or False

    if not path:
        return False

    if exact_path:
        return path == href

    return href in path
