"""Account completion after the first ORCID sign-in of an invited user.

The user signs in only once the form is saved. Until then, the pending
completion lives in the session that went through the ORCID callback, for
COMPLETION_MAX_AGE seconds."""

import secrets
from typing import TypedDict, cast

from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.crypto import constant_time_compare

from euphro_auth.models import User

COMPLETION_SESSION_KEY = "orcid_completion"
COMPLETION_MAX_AGE = 15 * 60


class PendingCompletion(TypedDict):
    token: str
    user_id: int
    account_id: int
    details: dict[str, str]
    created_at: int


def start_completion(
    request: HttpRequest, sociallogin: SocialLogin
) -> HttpResponseRedirect:
    token = secrets.token_urlsafe(32)
    user = sociallogin.user
    pending: PendingCompletion = {
        "token": token,
        "user_id": user.pk,
        "account_id": sociallogin.account.pk,
        "details": {
            field: str(getattr(user, field, "") or "")
            for field in ("email", "first_name", "last_name")
        }
        | {
            # Values returned by ORCID, which the form proposes.
            field: value
            for field, value in sociallogin.account.get_provider()
            .extract_common_fields(sociallogin.account.extra_data)
            .items()
            if field in ("email", "first_name", "last_name")
        },
        "created_at": int(timezone.now().timestamp()),
    }
    request.session[COMPLETION_SESSION_KEY] = pending
    return redirect("complete_registration_orcid", token)


def clear_completion(request: HttpRequest) -> None:
    request.session.pop(COMPLETION_SESSION_KEY, None)


def pending_completion(
    request: HttpRequest, token: str
) -> tuple[User, SocialAccount, dict[str, str]] | None:
    pending = request.session.get(COMPLETION_SESSION_KEY)
    if not isinstance(pending, dict) or not constant_time_compare(
        str(pending.get("token", "")), token
    ):
        return None
    pending = cast(PendingCompletion, pending)
    age = timezone.now().timestamp() - pending["created_at"]
    if not 0 <= age < COMPLETION_MAX_AGE:
        return None
    user = User.objects.filter(
        pk=pending["user_id"], is_active=True, invitation_completed_at__isnull=True
    ).first()
    account = SocialAccount.objects.filter(
        pk=pending["account_id"], user_id=pending["user_id"], provider="orcid"
    ).first()
    if user is None or account is None:
        return None
    return user, account, pending["details"]
