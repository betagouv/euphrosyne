"""Claims describing a user in the tokens Euphrosyne issues: the same in the
session token of the web front end and in OpenID Connect access tokens."""

from typing import Any

from lab.permissions import is_lab_admin

from ..models import User


def user_claims(user: User) -> dict[str, Any]:
    """Projects and role read by the Tools API. Tokens are only issued to a
    session that went through AccountGatesMiddleware (second factor of
    administrators included), so consumers only read ``is_admin``."""
    return {
        "projects": list(
            user.project_set.values("id", "name", "slug")  # type: ignore[misc]
        ),
        "is_admin": is_lab_admin(user),
    }
