from typing import Any

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from social_core.exceptions import AuthForbidden
from social_core.pipeline.partial import partial
from social_core.pipeline.social_auth import associate_user as social_associate_user
from social_core.pipeline.social_auth import social_user as social_social_user
from social_core.utils import PARTIAL_TOKEN_SESSION_NAME
from social_django.models import Partial, UserSocialAuth
from social_django.strategy import DjangoStrategy

from euphro_auth.models import User

from .backends import ORCIDOAuth2
from .invitations import (
    INVITATION_SESSION_KEY,
    clear_invitation,
    clear_partial,
    registration_partial,
    reject_invitation,
    validated_invitation_user,
)


def social_user(
    strategy: DjangoStrategy,
    backend: ORCIDOAuth2,
    uid: str,
    *args: Any,
    user: User | None = None,  # pylint: disable=unused-argument
    **kwargs: Any,
) -> dict[str, Any] | HttpResponseRedirect:
    # The authenticated browser user cannot authorize a new association either.
    out = social_social_user(backend, uid, None, *args, **kwargs)
    if INVITATION_SESSION_KEY in strategy.request.session:
        # Keep invitation validation, native association and consumption together
        # so concurrent callbacks cannot attach two identities to one invitation.
        with transaction.atomic():
            target = validated_invitation_user(
                strategy.request, for_callback=True, lock=True
            )
            if target is None or (out["social"] and out["social"].user_id != target.pk):
                return reject_invitation(strategy.request)
            out.update(
                social_associate_user(
                    backend, uid, target, **kwargs  # type: ignore[arg-type]
                )
                or {}
            )
            out["is_new"] = False
            clear_invitation(strategy.request)
    if not out.get("user"):
        messages.warning(
            strategy.request,
            _(
                # pylint: disable=line-too-long
                "Your ORCID account isn't connected to an existing account. Please use email/password to sign in, or register with ORCID first using the link you received in the invitation email."
            ),
        )
        return redirect("admin:login")
    return out


@partial
def complete_information(
    strategy: DjangoStrategy,
    backend: ORCIDOAuth2,
    current_partial: Partial,
    user: User,
    social: UserSocialAuth,
    *args: Any,
    **kwargs: Any,
):  # pylint: disable=unused-argument
    saved_token = strategy.session_get(PARTIAL_TOKEN_SESSION_NAME)
    # Social Auth may supply the authenticated browser user when resuming a
    # partial. It must still match the account associated with this ORCID.
    if (
        (saved_token and registration_partial(strategy.request, saved_token) is None)
        or not user
        or not social
        or user.pk != social.user_id
    ):
        clear_invitation(strategy.request)
        clear_partial(strategy.request)
        # A redirect from @partial would save a new continuation on rejection.
        # Use the native exception handler to abort without storing another one.
        raise AuthForbidden(backend)
    if not user.invitation_completed_at:
        return redirect(
            reverse("complete_registration_orcid", args=[current_partial.token])
        )
    return None
