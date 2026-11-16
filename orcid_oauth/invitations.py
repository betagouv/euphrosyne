"""The invitation is the server-side authority for a new ORCID association."""

from typing import TypedDict, cast

from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User

INVITATION_SESSION_KEY = "orcid_invitation"
CONTEXT_MAX_AGE = 15 * 60


class InvitationContext(TypedDict):
    user_id: int
    token: str
    validated_at: int


def clear_invitation(request: HttpRequest) -> None:
    request.session.pop(INVITATION_SESSION_KEY, None)


def invitation_is_usable(user: User, token: str) -> bool:
    return bool(
        user.is_active
        and user.invitation_completed_at is None
        and default_token_generator.check_token(user, token)
        and not SocialAccount.objects.filter(user=user, provider="orcid").exists()
    )


def store_invitation(request: HttpRequest, user: User, token: str) -> None:
    clear_invitation(request)
    if not invitation_is_usable(user, token):
        return
    # Only a validated invitation link can authorize a target. Browser fields
    # and generic session fields never cross this boundary.
    request.session.cycle_key()
    context: InvitationContext = {
        "user_id": user.pk,
        "token": token,
        "validated_at": int(timezone.now().timestamp()),
    }
    request.session[INVITATION_SESSION_KEY] = context


def validated_invitation_user(
    request: HttpRequest, *, lock: bool = False
) -> User | None:
    context = request.session.get(INVITATION_SESSION_KEY)
    if isinstance(context, dict):
        issued_at = context.get("validated_at")
        current = (
            isinstance(issued_at, int)
            and 0 <= timezone.now().timestamp() - issued_at < CONTEXT_MAX_AGE
            and isinstance(context.get("user_id"), int)
            and isinstance(context.get("token"), str)
        )
        if current:
            context = cast(InvitationContext, context)
            users = User.objects.select_for_update() if lock else User.objects
            user = users.filter(pk=context["user_id"]).first()
            if user and invitation_is_usable(user, context["token"]):
                return user
    clear_invitation(request)
    return None


def reject_invitation(request: HttpRequest) -> HttpResponseRedirect:
    clear_invitation(request)
    messages.warning(
        request,
        _(
            "Your ORCID registration invitation is invalid or has expired. "
            "Please reopen a valid invitation link."
        ),
    )
    return redirect("account_login")
