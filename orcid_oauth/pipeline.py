from typing import Any

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from social_core.pipeline.partial import partial
from social_core.pipeline.social_auth import associate_user as social_associate_user
from social_core.pipeline.social_auth import social_user as social_social_user
from social_django.models import Partial
from social_django.strategy import DjangoStrategy

from euphro_auth.models import User

from .backends import ORCIDOAuth2
from .invitations import (
    INVITATION_SESSION_KEY,
    clear_invitation,
    reject_invitation,
    store_registration,
    validated_invitation_user,
)


def social_user(
    strategy: DjangoStrategy,
    backend: ORCIDOAuth2,
    uid: str,
    *args,
    user: User | None = None,  # pylint: disable=unused-argument
    **kwargs,
) -> dict[str, Any] | HttpResponseRedirect:
    # Neither request identifiers nor an already authenticated browser user can
    # authorize a new association. Only the validated invitation can select it.
    out = social_social_user(backend, uid, None, *args, **kwargs)
    if INVITATION_SESSION_KEY in strategy.request.session:
        target = validated_invitation_user(strategy.request, for_callback=True)
        if target is None or (out["social"] and out["social"].user_id != target.pk):
            return reject_invitation(strategy.request)
        out["user"] = target
    if not out.get("user") and not out.get("social"):
        messages.warning(
            strategy.request,
            _(
                # pylint: disable=line-too-long
                "Your ORCID account isn't connected to an existing account. Please use email/password to sign in, or register with ORCID first using the link you received in the invitation email."
            ),
        )
        return redirect("admin:login")
    return out


def associate_user(
    strategy: DjangoStrategy,
    backend: ORCIDOAuth2,
    uid: str,
    user: User | None = None,
    social: Any = None,
    **kwargs: Any,
) -> dict[str, Any] | HttpResponseRedirect | None:
    if social:
        return None
    # Serialize associations for this target. Concurrent callbacks or an old
    # session snapshot cannot use the same invitation to attach a second ORCID.
    with transaction.atomic():
        target = validated_invitation_user(
            strategy.request, for_callback=True, lock=True
        )
        if target is None or user is None or target.pk != user.pk:
            return reject_invitation(strategy.request)
        # Social Core's protocol requires a username; our email-only Django user
        # has none, while the association step only needs its primary key.
        result = social_associate_user(
            backend,
            uid,
            target,  # type: ignore[arg-type]
            **kwargs,
        )
        clear_invitation(strategy.request)
        return result


@partial
def complete_information(
    strategy: DjangoStrategy,
    current_partial: Partial,
    user: User,
    uid: str,
    *args: Any,
    **kwargs: Any,
):  # pylint: disable=unused-argument
    if user and not user.invitation_completed_at:
        store_registration(strategy.request, user, uid, current_partial.token)
        return redirect(
            reverse("complete_registration_orcid", args=[current_partial.token])
        )
    # continue the pipeline
    return None
