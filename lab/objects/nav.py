from typing import List, Optional


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
        extra_path: Optional[List[str]] = None,
        exact_path: bool = False,
        badge: int = 0,
    ):
        self.title = title
        self.href = href
        self.icon = icon
        self.extra_path = extra_path
        self.exact_path = exact_path
        self.badge = badge

    def __str__(self) -> str:
        return f"NavItem({self.title}, {self.href})"
