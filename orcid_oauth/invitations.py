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

from .completion import clear_completion

INVITATION_SESSION_KEY = "orcid_invitation"
CONTEXT_MAX_AGE = 15 * 60


class InvitationContext(TypedDict):
    user_id: int
    token: str
    validated_at: int
    session_key: str | None
    oauth_state: str | None


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
    clear_completion(request)
    if not invitation_is_usable(user, token):
        return
    # Only a validated invitation link can authorize a target. Browser fields
    # and generic session fields never cross this boundary.
    request.session.cycle_key()
    context: InvitationContext = {
        "user_id": user.pk,
        "token": token,
        "validated_at": int(timezone.now().timestamp()),
        "session_key": request.session.session_key,
        "oauth_state": None,
    }
    request.session[INVITATION_SESSION_KEY] = context


def validated_invitation_user(
    request: HttpRequest,
    *,
    for_callback: bool = False,
    oauth_state: str | None = None,
    lock: bool = False,
) -> User | None:
    context = request.session.get(INVITATION_SESSION_KEY)
    if isinstance(context, dict):
        issued_at = context.get("validated_at")
        current = (
            isinstance(issued_at, int)
            and 0 <= timezone.now().timestamp() - issued_at < CONTEXT_MAX_AGE
            and context.get("session_key")
            and context["session_key"] == request.session.session_key
            and isinstance(context.get("user_id"), int)
            and isinstance(context.get("token"), str)
        )
        # allauth validates the incoming OAuth state. A session can hold
        # several attempts, so bind this callback's state to the invitation
        # selected at signup start.
        started = not for_callback or bool(
            oauth_state and context.get("oauth_state") == oauth_state
        )
        if current and started:
            context = cast(InvitationContext, context)
            users = User.objects.select_for_update() if lock else User.objects
            user = users.filter(pk=context["user_id"]).first()
            if user and invitation_is_usable(user, context["token"]):
                return user
    clear_invitation(request)
    return None


def reject_invitation(request: HttpRequest) -> HttpResponseRedirect:
    clear_invitation(request)
    clear_completion(request)
    messages.warning(
        request,
        _(
            "Your ORCID registration invitation is invalid or has expired. "
            "Please reopen a valid invitation link."
        ),
    )
    return redirect("admin:login")
