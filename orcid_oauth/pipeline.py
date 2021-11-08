from typing import Any, Mapping

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from social_core.pipeline.partial import partial
from social_core.pipeline.social_auth import social_user as social_social_user
from social_django.strategy import DjangoStrategy

from euphro_auth.models import User

from .backends import ORCIDOAuth2


def social_user(
    strategy: DjangoStrategy,
    backend: ORCIDOAuth2,
    uid: str,
    *args,
    user: User = None,
    **kwargs,
):
    user_id = strategy.session_get("user_id")
    if user_id:
        user = get_user_model().objects.get(id=user_id)
    return social_social_user(backend, uid, user, *args, **kwargs)


@partial
def complete_information(
    current_partial: Mapping[str, Any], user: User, *args, **kwargs
):  # pylint: disable=unused-argument
    if user and not user.invitation_completed_at:
        # redirect to a view where the user can verify
        # the information received from ORCID
        return redirect(
            reverse("complete_registration_orcid", args=[current_partial.token])
        )
    # continue the pipeline
    return None
