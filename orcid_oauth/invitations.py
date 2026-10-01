"""Server-only authority for ORCID invitation and registration continuations."""

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
REGISTRATION_SESSION_KEY = "orcid_registration"
CONTEXT_MAX_AGE = 15 * 60


class InvitationContext(TypedDict):
    user_id: int
    token: str
    validated_at: int
    session_key: str | None
    oauth_state: str | None


class RegistrationContext(TypedDict):
    user_id: int
    uid: str
    partial_token: str
    validated_at: int
    session_key: str | None


def clear_invitation(request: HttpRequest) -> None:
    request.session.pop(INVITATION_SESSION_KEY, None)


def clear_registration(request: HttpRequest) -> None:
    request.session.pop(REGISTRATION_SESSION_KEY, None)
    request.session.pop(PARTIAL_TOKEN_SESSION_NAME, None)


def invitation_is_usable(user: User, token: str) -> bool:
    # The existing invitation token remains the source of truth. An association
    # also makes it unusable, even before the information form is completed.
    return bool(
        user.is_active
        and user.invitation_completed_at is None
        and default_token_generator.check_token(user, token)
        and not user.social_auth.filter(provider="orcid").exists()
    )


def store_invitation(request: HttpRequest, user: User, token: str) -> None:
    clear_invitation(request)
    clear_registration(request)
    if not invitation_is_usable(user, token):
        return
    # Only a validated invitation link can cross this security boundary. Never
    # derive the target from form fields or Python Social Auth's generic session.
    request.session.cycle_key()
    context: InvitationContext = {
        "user_id": user.pk,
        "token": token,
        "validated_at": int(timezone.now().timestamp()),
        "session_key": request.session.session_key,
        "oauth_state": None,
    }
    request.session[INVITATION_SESSION_KEY] = context


def context_is_current(request: HttpRequest, context: object) -> bool:
    if not isinstance(context, dict):
        return False
    issued_at = context.get("validated_at")
    return bool(
        isinstance(issued_at, int)
        and not isinstance(issued_at, bool)
        and 0 <= timezone.now().timestamp() - issued_at < CONTEXT_MAX_AGE
        and context.get("session_key")
        and context["session_key"] == request.session.session_key
        and isinstance(context.get("user_id"), int)
        and not isinstance(context.get("user_id"), bool)
    )


def validated_invitation_user(
    request: HttpRequest, *, for_callback: bool = False, lock: bool = False
) -> User | None:
    context = request.session.get(INVITATION_SESSION_KEY)
    if context_is_current(request, context):
        context = cast(InvitationContext, context)
        users = User.objects.select_for_update() if lock else User.objects
        user = users.filter(pk=context["user_id"]).first()
        token = context.get("token")
        state = context.get("oauth_state")
        state_valid = not for_callback or bool(
            state
            and state == request.session.get("orcid_state")
            and state == (request.GET.get("state") or request.POST.get("state"))
        )
        if (
            user
            and isinstance(token, str)
            and invitation_is_usable(user, token)
            and state_valid
        ):
            return user
    clear_invitation(request)
    return None


def reject_invitation(request: HttpRequest) -> HttpResponseRedirect:
    clear_invitation(request)
    clear_registration(request)
    messages.warning(
        request,
        _(
            "Your ORCID registration invitation is invalid or has expired. "
            "Please reopen a valid invitation link."
        ),
    )
    return redirect("admin:login")


def store_registration(
    request: HttpRequest, user: User, uid: str, partial_token: str
) -> None:
    # The pipeline has already authenticated this ORCID identity and associated
    # it with the validated target. This continuation cannot authorize another
    # association; it only permits completing that same account's information.
    context: RegistrationContext = {
        "user_id": user.pk,
        "uid": uid,
        "partial_token": partial_token,
        "validated_at": int(timezone.now().timestamp()),
        "session_key": request.session.session_key,
    }
    request.session[REGISTRATION_SESSION_KEY] = context


def validated_registration_partial(request: HttpRequest, token: str) -> Partial | None:
    context = request.session.get(REGISTRATION_SESSION_KEY)
    if not context_is_current(request, context):
        clear_registration(request)
        return None
    context = cast(RegistrationContext, context)
    if (
        context.get("partial_token") != token
        or request.session.get(PARTIAL_TOKEN_SESSION_NAME) != token
    ):
        clear_registration(request)
        return None
    partial = load_strategy(request).partial_load(token)
    if partial and partial.backend == "orcid":
        user = partial.kwargs.get("user")
        social = partial.kwargs.get("social")
        if (
            user
            and user.is_active
            and user.pk == context["user_id"]
            and social
            and social.user_id == user.pk
        ):
            if social.provider == "orcid" and social.uid == context.get("uid"):
                return partial
    clear_registration(request)
    return None
