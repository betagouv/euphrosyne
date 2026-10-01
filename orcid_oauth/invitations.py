"""The invitation is the server-side authority for a new ORCID association."""

from typing import TypedDict, cast

from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from social_core.utils import PARTIAL_TOKEN_SESSION_NAME
from social_django.models import Partial
from social_django.utils import load_strategy

from euphro_auth.models import User

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


def clear_partial(request: HttpRequest) -> None:
    strategy = load_strategy(request)
    token = strategy.session_get(PARTIAL_TOKEN_SESSION_NAME)
    if token:
        strategy.clean_partial_pipeline(token)


def registration_partial(request: HttpRequest, token: str) -> Partial | None:
    # The custom form is outside Social Auth's callback view, so check the
    # session-owned token before loading its server-stored partial.
    if token != request.session.get(PARTIAL_TOKEN_SESSION_NAME):
        return None
    saved = load_strategy(request).partial_load(token)
    if saved and saved.backend == "orcid":
        age = (timezone.now() - saved.timestamp).total_seconds()
        user = saved.kwargs.get("user")
        social = saved.kwargs.get("social")
        if 0 <= age < CONTEXT_MAX_AGE and user and user.is_active:
            if social and social.user_id == user.pk:
                return saved
    return None


def invitation_is_usable(user: User, token: str) -> bool:
    return bool(
        user.is_active
        and user.invitation_completed_at is None
        and default_token_generator.check_token(user, token)
        and not user.social_auth.filter(provider="orcid").exists()
    )


def store_invitation(request: HttpRequest, user: User, token: str) -> None:
    clear_invitation(request)
    clear_partial(request)
    if not invitation_is_usable(user, token):
        return
    # Only a validated invitation link can authorize a target. Browser fields
    # and Python Social Auth's generic session fields never cross this boundary.
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
    request: HttpRequest, *, for_callback: bool = False, lock: bool = False
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
        # Social Auth validates the incoming OAuth state. Here we only bind its
        # server-generated state to the invitation selected at signup start.
        started = not for_callback or bool(
            context.get("oauth_state")
            and context["oauth_state"] == request.session.get("orcid_state")
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
    clear_partial(request)
    messages.warning(
        request,
        _(
            "Your ORCID registration invitation is invalid or has expired. "
            "Please reopen a valid invitation link."
        ),
    )
    return redirect("admin:login")
