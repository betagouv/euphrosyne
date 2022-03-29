from typing import Optional

from django import template
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

register = template.Library()


# pylint: disable-msg=too-many-arguments
class NavItem:
    """
    Helper object to more easily path item info from sidebar_items to nav_item
    """

    def __init__(
        self,
        title: str,
        href: str,
        icon: str,
        extra_path: Optional[list[str]] = None,
        exact_path: bool = False,
        badge: int = 0,
    ):
        self.title = title
        self.href = href
        self.icon = icon
        self.extra_path = extra_path or []
        self.exact_path = exact_path
        self.badge = badge

    def __str__(self) -> str:
        return f"NavItem({self.title}, {self.href})"


@register.inclusion_tag("components/nav/nav_items.html")
def sidebar_items(request: HttpRequest):
    """
    Inclustion tag to display the whole side navigation.

    Parameters
    ----------
    request : HttpRequest
    """
    items: list[NavItem] = [
        NavItem(
            _("Projects"),
            reverse("admin:lab_project_changelist"),
            '<i class="ri-folder-open-line" aria-hidden="true"></i>',
            [reverse("admin:lab_run_changelist")],
        )
    ]

    if request.user and request.user.is_lab_admin:
        items.append(
            NavItem(
                _("Users"),
                reverse("admin:euphro_auth_user_changelist"),
                '<i class="ri-user-line" aria-hidden="true"></i>',
            )
        )
        items.append(
            NavItem(
                _("Invitations"),
                reverse("admin:euphro_auth_userinvitation_changelist"),
                '<i class="ri-mail-line" aria-hidden="true"></i>',
            )
        )

    return {"request": request, "items": items}


@register.inclusion_tag("components/nav/nav_item.html")
def nav_item(current_path: str, item: NavItem):
    """
    Tag to get a nav item components

    Parameters
    ----------
    current_path : str
        Current path of the page, used to check if this nav_item
        is representing the current one
    item : NavItem
        Info to create that nav_item.html template
    """

    current_page = False

    if item.exact_path:
        current_page = item.href == current_path
    else:
        all_path = [item.href] + item.extra_path
        match_urls = map(lambda path: path in current_path, all_path)
        current_page = any(match_urls)

    return {
        "title": item.title,
        "icon": item.icon,
        "href": item.href,
        "badge": item.badge,
        "current_page": current_page,
    }
