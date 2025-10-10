from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from social_core.pipeline.partial import partial
from social_core.pipeline.social_auth import social_user as social_social_user
from social_django.models import Partial
from social_django.strategy import DjangoStrategy

from euphro_auth.models import User

from .backends import ORCIDOAuth2


def social_user(
    strategy: DjangoStrategy,
    backend: ORCIDOAuth2,
    uid: str,
    *args,
    user: User | None = None,
    **kwargs,
):
    user_id = strategy.session_get("user_id")
    if user_id:
        user = get_user_model().objects.get(id=user_id)
    out = social_social_user(backend, uid, user, *args, **kwargs)  # type: ignore
    if not out.get("user") and not out.get("social"):
        messages.warning(
            strategy.request,
            _(
                # pylint: disable=line-too-long
                "Your ORCID account isn't connected to an existing account. Please use email/password to sign in, or register with ORCID first using the link you received in the invitation email."
            ),
        )
    return out


@partial
def complete_information(
    current_partial: Partial, user: User, *args, **kwargs
):  # pylint: disable=unused-argument
    if user and not user.invitation_completed_at:
        # redirect to a view where the user can verify
        # the information received from ORCID
        return redirect(
            reverse("complete_registration_orcid", args=[current_partial.token])
        )
    # continue the pipeline
    return None
