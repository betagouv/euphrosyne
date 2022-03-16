from typing import List

from django import template
from django.http import HttpRequest

register = template.Library()


@register.inclusion_tag('components/nav/nav_item.html', takes_context=True)
def nav_item(context, title: str, href: str, icon: str, *args, **kwargs):
    """
    Tag to get a nav item components

    Parameters
    ----------
    context : any
        Get the page context automatically, usefull to get the request
    title : str
        Title of the nav item
    href : str
        Where to send the user
    icon : str
        HTML code for the icon
    **kwargs :
        Dictionary of options

    Keyword Args
    ------------
        badge : int, optional
            Set to show a badge in the nav item (default=0)
        exact_path : bool, optional
            Tell wether the `href` and the `path` must be equal (default=False)
        extra_path : List[str], optional
            List of other url to check if the nav item is for this current page
    """
    request: HttpRequest = context["request"]

    badge: int = kwargs.get("badge", 0)
    exact_path: bool = kwargs.get("exact_path", False)
    extra_path: List[str] = kwargs.get("extra_path", [])

    all_path = [href] + extra_path

    current_page = False

    if exact_path:
        current_page = href == request.path
    else:
        match_urls = map(lambda path: path in request.path, all_path)
        current_page = any(match_urls)

    return {
        "title": title,
        "icon": icon,
        "href": href,
        "badge": badge,
        "current_page": current_page
    }
